from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, HTMLResponse
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import uuid

from .config import APP_NAME, APP_VERSION, WORKSPACES_DIR
from .database import init_db, connect
from .schemas import ProjectCreate, AnalysisGroupCreate, GitLabGroupAnalysisCreate
from .engines import clone_repository
from .deep_analysis import build_analysis_markdown
from .functional_analysis import build_analysis_html
from .agents import AnalysisContext
from .supervisor import default_supervisor
from .communication import SharedStore
from . import llm
from .analysis_orchestrator import run_group_analysis
from .gitlab import gitlab_settings, list_accessible_groups, list_group_projects
from .schemas import BugReportExportRequest
from .bug_report import TASKS, _sorted_findings, build_bug_export_html

app = FastAPI(title=APP_NAME, version=APP_VERSION,
 description="Orquestador de análisis estático profundo de uno o varios microservicios. No ejecuta el código analizado.")

@app.on_event("startup")
def startup():
    init_db()
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS analysis_groups (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, repositories_json TEXT NOT NULL,
          status TEXT NOT NULL, created_at TEXT NOT NULL, analysis_json TEXT, last_error TEXT)""")

def now(): return datetime.now(timezone.utc).isoformat()

def run_analysis(project_id: str):
    with connect() as con:
        row=con.execute("SELECT * FROM projects WHERE id=?",(project_id,)).fetchone()
        if not row: return
        con.execute("UPDATE projects SET status='CLONING',last_error=NULL WHERE id=?",(project_id,))
        git_url,name=row["git_url"],row["name"]
    try:
        source=clone_repository(project_id,git_url)
        with connect() as con: con.execute("UPDATE projects SET status='ANALYZING' WHERE id=?",(project_id,))
        context = AnalysisContext(root=source, repository=name, store=SharedStore(WORKSPACES_DIR/project_id/"agent-runs", run_id=project_id))
        # El análisis individual no incluye calidad: se pide al supervisor solo lo necesario
        # (los agentes LLM se omiten solos si no están activados).
        default_supervisor().run(context, only=["inventory", "deep_analysis", "functional_analysis", "java_analysis",
            "llm_functional_interpretation", "llm_architecture_explanation"])
        inventory = context.results["inventory"]; deep = context.results["deep_analysis"]
        functional = context.results["functional_analysis"]; java = context.results["java_analysis"]
        analysis={"analysis_version":"5.0","functional_analysis":functional,"project_name":name,
          "source_path":str(source),"repository_inventory":inventory,"deep_analysis":deep,
          "java_analysis":java,
          "agent_insights":{k:v for k,v in context.results.items() if k not in ("inventory","deep_analysis","functional_analysis","java_analysis")},
          "completion_status":"STATIC_ANALYSIS_COMPLETED","runtime_validation":"NOT_PERFORMED"}
        folder=WORKSPACES_DIR/project_id; folder.mkdir(parents=True,exist_ok=True)
        (folder/"analysis.json").write_text(json.dumps(analysis,indent=2,ensure_ascii=False),encoding="utf-8")
        report=build_analysis_markdown(name,inventory,deep)
        report+="\n## Análisis funcional\n"+json.dumps(functional.get("summary",{}),ensure_ascii=False,indent=2)
        report+="\n\n## Análisis Java / Spring\n"+json.dumps(java.get("summary",{}),ensure_ascii=False,indent=2)
        (folder/"analysis.md").write_text(report,encoding="utf-8")
        (folder/"analysis.html").write_text(build_analysis_html(name,analysis),encoding="utf-8")
        with connect() as con:
            con.execute("UPDATE projects SET status='ANALYSIS_COMPLETED',source_path=?,analysis_json=?,reconstruction_json=NULL,last_error=NULL WHERE id=?",
              (str(source),json.dumps(analysis,ensure_ascii=False),project_id))
    except Exception as exc:
        with connect() as con: con.execute("UPDATE projects SET status='FAILED',last_error=? WHERE id=?",(str(exc),project_id))

def run_analysis_group(group_id: str):
    with connect() as con:
        row=con.execute("SELECT * FROM analysis_groups WHERE id=?",(group_id,)).fetchone()
        if not row: return
        con.execute("UPDATE analysis_groups SET status='ANALYZING',last_error=NULL WHERE id=?",(group_id,))
        name,repositories=row["name"],json.loads(row["repositories_json"])
    try:
        # The token is loaded at execution time and is never persisted in SQLite or report data.
        token=os.getenv("GITLAB_TOKEN","").strip()
        host=None
        if token:
            _,_,host=gitlab_settings()
        analysis=run_group_analysis(group_id,name,repositories,clone_token=token or None,clone_host=host)
        status="ANALYSIS_COMPLETED" if not analysis["failures"] else "PARTIAL_ANALYSIS_COMPLETED"
        with connect() as con:
            con.execute("UPDATE analysis_groups SET status=?,analysis_json=?,last_error=NULL WHERE id=?",
              (status,json.dumps(analysis,ensure_ascii=False),group_id))
    except Exception as exc:
        with connect() as con: con.execute("UPDATE analysis_groups SET status='FAILED',last_error=? WHERE id=?",(str(exc),group_id))

@app.get("/")
def root():
    return {"application":APP_NAME,"version":APP_VERSION,"mode":"deep_analysis_orchestrator",
      "message":"Usa /api/projects para un servicio, /api/analysis-groups para una lista o /api/gitlab/groups/{group_id}/analysis para un grupo GitLab.","documentation":"/docs"}

# El lanzador compara esta hora con la de los ficheros de código para reiniciar una API obsoleta.
STARTED_AT=datetime.now(timezone.utc).isoformat()
STARTED_EPOCH=int(datetime.now(timezone.utc).timestamp())

@app.get("/health")
def health(): return {"status":"ok","version":APP_VERSION,"mode":"deep_analysis_orchestrator","started_at":STARTED_AT,"started_epoch":STARTED_EPOCH,"llm":llm.status()}

@app.get("/api/llm")
def get_llm_configuration():
    """Proveedor y modelo activos para los agentes LLM (sin claves)."""
    return llm.status()

@app.get("/api/llm/models")
def get_llm_models(provider: str | None = None):
    """Modelos que ofrece el proveedor configurado (o el indicado) a esta cuenta."""
    try: return {"provider": llm.normalize_provider(provider or os.getenv("LLM_PROVIDER")), "models": llm.list_models(provider=provider)}
    except llm.LLMError as exc: raise HTTPException(400, str(exc))

@app.post("/api/projects",status_code=202)
def create_project(payload:ProjectCreate,background_tasks:BackgroundTasks):
    project_id=str(uuid.uuid4())
    with connect() as con:
        con.execute("INSERT INTO projects(id,name,git_url,status,created_at) VALUES(?,?,?,?,?)",
          (project_id,payload.name,payload.git_url,"QUEUED",now()))
    background_tasks.add_task(run_analysis,project_id)
    return {"project_id":project_id,"status":"QUEUED","message":"Análisis individual profundo iniciado."}

def persist_analysis_group(name: str, repositories: list[dict], background_tasks: BackgroundTasks):
    group_id=str(uuid.uuid4())
    with connect() as con:
        con.execute("INSERT INTO analysis_groups(id,name,repositories_json,status,created_at) VALUES(?,?,?,?,?)",
          (group_id,name,json.dumps(repositories,ensure_ascii=False),"QUEUED",now()))
    background_tasks.add_task(run_analysis_group,group_id)
    return {"analysis_group_id":group_id,"status":"QUEUED","repository_count":len(repositories)}

@app.post("/api/analysis-groups",status_code=202)
def create_analysis_group(payload:AnalysisGroupCreate,background_tasks:BackgroundTasks):
    return persist_analysis_group(payload.name,[x.model_dump() for x in payload.repositories],background_tasks)

@app.get("/api/gitlab/groups")
def get_gitlab_groups():
    """List groups and subgroups visible to the configured GitLab token."""
    try:
        gitlab_settings()
        return list_accessible_groups()
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"No se pudieron consultar los grupos de GitLab: {exc}")

@app.get("/api/gitlab/groups/{group_id}/projects")
def get_gitlab_group_projects(group_id: str):
    """List cloneable repositories in a group, including its subgroups."""
    try:
        gitlab_settings()
        return list_group_projects(group_id, allow_empty=True)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"No se pudieron consultar los repositorios del grupo: {exc}")

@app.post("/api/gitlab/groups/{group_id}/analysis",status_code=202)
def create_gitlab_group_analysis(group_id:str,payload:GitLabGroupAnalysisCreate,background_tasks:BackgroundTasks):
    try:
        # Validate credentials/configuration before accepting the job.
        gitlab_settings()
        repositories=list_group_projects(group_id, allow_empty=True)
        if payload.project_ids is not None:
            requested = set(payload.project_ids)
            available = {item.get("gitlab_project_id") for item in repositories}
            unknown = requested - available
            if unknown:
                raise HTTPException(400, "Hay identificadores de proyecto que no pertenecen al grupo seleccionado: " + ", ".join(map(str, sorted(unknown))))
            repositories = [item for item in repositories if item.get("gitlab_project_id") in requested]
        if not repositories:
            raise HTTPException(400, "No hay repositorios seleccionados para analizar.")
    except HTTPException:
        raise
    except (ValueError,RuntimeError) as exc:
        raise HTTPException(400,str(exc))
    except Exception as exc:
        raise HTTPException(502,f"No se pudo consultar GitLab: {exc}")
    name=payload.name or f"gitlab-group-{group_id}"
    return persist_analysis_group(name,repositories,background_tasks)

@app.get("/api/analysis-groups")
def list_analysis_groups():
    with connect() as con:
        rows=con.execute("SELECT id,name,status,created_at,last_error FROM analysis_groups ORDER BY created_at DESC").fetchall()
    return [dict(x) for x in rows]

@app.get("/api/analysis-groups/{group_id}")
def get_analysis_group(group_id:str):
    with connect() as con: row=con.execute("SELECT * FROM analysis_groups WHERE id=?",(group_id,)).fetchone()
    if not row: raise HTTPException(404,"Grupo de análisis no encontrado")
    result=dict(row); result["repositories"]=json.loads(result.pop("repositories_json"))
    if result.get("analysis_json"): result["analysis"]=json.loads(result.pop("analysis_json"))
    return result

@app.get("/api/analysis-groups/{group_id}/progress")
def get_analysis_group_progress(group_id:str):
    """Estado ligero para la barra de progreso: repositorios terminados, reutilizados y fallidos."""
    with connect() as con: row=con.execute("SELECT status,last_error FROM analysis_groups WHERE id=?",(group_id,)).fetchone()
    if not row: raise HTTPException(404,"Grupo de análisis no encontrado")
    path=WORKSPACES_DIR/group_id/"progress.json"
    try: progress=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError): progress=None
    return {"status":row["status"],"last_error":row["last_error"],"progress":progress}

@app.get("/api/analysis-groups/{group_id}/analysis")
def get_analysis_group_result(group_id:str):
    with connect() as con: row=con.execute("SELECT status,analysis_json,last_error FROM analysis_groups WHERE id=?",(group_id,)).fetchone()
    if not row: raise HTTPException(404,"Grupo de análisis no encontrado")
    if not row["analysis_json"]: return {"analysis_group_id":group_id,"status":row["status"],"error":row["last_error"]}
    return json.loads(row["analysis_json"])

@app.get("/api/analysis-groups/{group_id}/agent-runs")
def get_analysis_group_agent_runs(group_id:str):
    """Estado, evidencias y errores de cada agente (manifiesto del almacén compartido)."""
    import re
    if not re.fullmatch(r"[A-Za-z0-9-]+", group_id):
        raise HTTPException(404,"Grupo de análisis no encontrado")
    path=WORKSPACES_DIR/group_id/"agent-runs"/"manifest.json"
    if not path.is_file(): raise HTTPException(409,"Todavía no hay ejecuciones de agentes registradas")
    return json.loads(path.read_text(encoding="utf-8"))

@app.get("/api/analysis-groups/{group_id}/report",response_class=PlainTextResponse)
def get_analysis_group_report(group_id:str):
    path=WORKSPACES_DIR/group_id/"analysis.md"
    if not path.is_file(): raise HTTPException(409,"Informe todavía no disponible")
    return path.read_text(encoding="utf-8")

@app.get("/api/analysis-groups/{group_id}/report.html",response_class=HTMLResponse)
def get_analysis_group_html(group_id:str):
    path=WORKSPACES_DIR/group_id/"analysis.html"
    if not path.is_file(): raise HTTPException(409,"Informe HTML todavía no disponible")
    return path.read_text(encoding="utf-8")

@app.get("/api/analysis-groups/{group_id}/activity.html",response_class=HTMLResponse)
def get_analysis_group_activity_html(group_id:str):
    path=WORKSPACES_DIR/group_id/"activity.html"
    if not path.is_file(): raise HTTPException(404,"Histórico de actividad no disponible (solo para grupos GitLab)")
    return path.read_text(encoding="utf-8")

@app.get("/api/analysis-groups/{group_id}/agents.html",response_class=HTMLResponse)
def get_analysis_group_agents_html(group_id:str):
    path=WORKSPACES_DIR/group_id/"agents.html"
    if not path.is_file(): raise HTTPException(409,"Informe multiagente todavía no disponible")
    return path.read_text(encoding="utf-8")

@app.get("/api/analysis-groups/{group_id}/repositories/{repository_slug}/activity.html",response_class=HTMLResponse)
def get_analysis_group_repository_activity_html(group_id: str, repository_slug: str):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", repository_slug):
        raise HTTPException(404, "Microservicio no encontrado")
    path = WORKSPACES_DIR/group_id/"repositories"/repository_slug/"activity.html"
    if not path.is_file():
        raise HTTPException(404, "Histórico de Git del microservicio no encontrado")
    return path.read_text(encoding="utf-8")

@app.get("/api/analysis-groups/{group_id}/repositories/{repository_slug}/agents.html",response_class=HTMLResponse)
def get_analysis_group_repository_agents_html(group_id: str, repository_slug: str):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", repository_slug):
        raise HTTPException(404, "Microservicio no encontrado")
    path = WORKSPACES_DIR/group_id/"repositories"/repository_slug/"agents.html"
    if not path.is_file():
        raise HTTPException(404, "Informe multiagente del microservicio no encontrado")
    return path.read_text(encoding="utf-8")

@app.get("/api/analysis-groups/{group_id}/documentation/index.html",response_class=HTMLResponse)
def get_analysis_group_documentation_index(group_id: str):
    path = WORKSPACES_DIR/group_id/"index.html"
    if not path.is_file():
        raise HTTPException(409, "El índice de documentación todavía no está disponible")
    return path.read_text(encoding="utf-8")


@app.get("/api/analysis-groups/{group_id}/repositories/{repository_slug}/report.html",response_class=HTMLResponse)
def get_analysis_group_repository_html(group_id: str, repository_slug: str):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", repository_slug):
        raise HTTPException(404, "Microservicio no encontrado")
    path = WORKSPACES_DIR/group_id/"repositories"/repository_slug/"analysis.html"
    if not path.is_file():
        raise HTTPException(404, "Ficha HTML del microservicio no encontrada")
    return path.read_text(encoding="utf-8")


@app.post("/api/analysis-groups/{group_id}/bug-reports/export")
def export_selected_bug_reports(group_id: str, payload: BugReportExportRequest):
    """Exporta hallazgos seleccionados de uno o varios microservicios del grupo."""
    import re
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", group_id):
        raise HTTPException(404, "Grupo de análisis no encontrado")

    total_selected = 0
    requested_reports = set()
    for selection in payload.selections:
        if selection.report_name in requested_reports:
            raise HTTPException(400, "No repitas el mismo informe en la selección.")
        requested_reports.add(selection.report_name)
        if len(set(selection.finding_indexes)) != len(selection.finding_indexes) or any(i < 0 for i in selection.finding_indexes):
            raise HTTPException(400, "La selección contiene índices duplicados o no válidos.")
        total_selected += len(selection.finding_indexes)
    if total_selected > 500:
        raise HTTPException(400, "La exportación admite un máximo de 500 hallazgos.")

    with connect() as con:
        group = con.execute("SELECT id FROM analysis_groups WHERE id=?", (group_id,)).fetchone()
    if not group:
        raise HTTPException(404, "Grupo de análisis no encontrado")

    analysis_path = WORKSPACES_DIR / group_id / "analysis.json"
    if not analysis_path.is_file():
        raise HTTPException(409, "El análisis todavía no está disponible para exportar.")
    try:
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise HTTPException(500, "No se pudo leer el resultado del análisis.")

    tasks, bugs = [], []
    repositories = analysis.get("repositories", [])
    for selection in payload.selections:
        expected_report = "bug-reports/" + selection.report_name
        repository = next((item for item in repositories if item.get("bug_report") == expected_report), None)
        if repository is None:
            raise HTTPException(404, "Uno de los informes no pertenece a este grupo de análisis.")
        findings = _sorted_findings(repository.get("quality_analysis") or {})
        if any(index >= len(findings) for index in selection.finding_indexes):
            raise HTTPException(400, "La selección contiene hallazgos que no existen.")
        service_slug = str(repository.get("artifact_dir", "")).split("/")[-1]
        for index in selection.finding_indexes:
            finding = findings[index]
            action = TASKS.get(finding.get("code"), "Revisar el hallazgo y añadir una prueba de regresión.")
            tasks.append({
                "id": f"{service_slug}-{index + 1}",
                "repository": repository.get("name", "microservicio"),
                "title": finding.get("title", "Posible bug"),
                "description": finding.get("description", ""),
                "status": "Pendiente",
                "severity": finding.get("severity", "low"),
                "file": finding.get("file", "N/D"),
                "line": finding.get("line", "N/D"),
                "recommended_action": action,
            })
            bugs.append({
                "repository": repository.get("name", "microservicio"),
                "code": finding.get("code", "N/D"),
                "title": finding.get("title", "Posible bug"),
                "description": finding.get("description", ""),
                "severity": finding.get("severity", "low"),
                "file": finding.get("file", "N/D"),
                "line": finding.get("line", "N/D"),
                "confidence": finding.get("confidence", "heuristic_candidate"),
                "excerpt": finding.get("excerpt", ""),
                "recommended_action": action,
            })

    generated = now()
    export_data = {
        "schema_version": "1.0",
        "analysis_group_id": group_id,
        "group_name": analysis.get("group_name", "analysis"),
        "generated_at": generated,
        "total_tasks": len(tasks),
        "total_bugs": len(bugs),
        "tasks": tasks,
        "bugs": bugs,
    }
    safe_id = group_id[:8]
    return {
        "status": "success",
        "json_filename": f"tareas-y-bugs-{safe_id}.json",
        "html_filename": f"informe-tareas-y-bugs-{safe_id}.html",
        "json_data": export_data,
        "html_content": build_bug_export_html(export_data),
    }

@app.get("/api/analysis-groups/{group_id}/bug-reports/index.html",response_class=HTMLResponse)
def get_analysis_group_bug_reports_index(group_id: str):
    path = WORKSPACES_DIR/group_id/"bug-reports"/"index.html"
    if not path.is_file():
        raise HTTPException(409, "El índice de informes de posibles bugs todavía no está disponible")
    return path.read_text(encoding="utf-8")


@app.get("/api/analysis-groups/{group_id}/bug-reports/{report_name}",response_class=HTMLResponse)
def get_analysis_group_bug_report(group_id: str, report_name: str):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.html", report_name):
        raise HTTPException(404, "Informe no encontrado")
    path = WORKSPACES_DIR/group_id/"bug-reports"/report_name
    if not path.is_file():
        raise HTTPException(404, "No existe un informe de posibles bugs para ese microservicio")
    return path.read_text(encoding="utf-8")


@app.get("/api/projects")
def list_projects():
    with connect() as con: rows=con.execute("SELECT id,name,status,created_at,last_error FROM projects ORDER BY created_at DESC").fetchall()
    return [dict(x) for x in rows]

@app.get("/api/projects/{project_id}")
def get_project(project_id:str):
    with connect() as con: row=con.execute("SELECT * FROM projects WHERE id=?",(project_id,)).fetchone()
    if not row: raise HTTPException(404,"Proyecto no encontrado")
    result=dict(row)
    if result.get("analysis_json"): result["analysis"]=json.loads(result.pop("analysis_json"))
    result.pop("reconstruction_json",None)
    return result

@app.get("/api/projects/{project_id}/analysis")
def get_analysis(project_id:str):
    with connect() as con: row=con.execute("SELECT status,analysis_json,last_error FROM projects WHERE id=?",(project_id,)).fetchone()
    if not row: raise HTTPException(404,"Proyecto no encontrado")
    if row["status"]!="ANALYSIS_COMPLETED" or not row["analysis_json"]:
        return {"project_id":project_id,"status":row["status"],"error":row["last_error"]}
    return json.loads(row["analysis_json"])

@app.get("/api/projects/{project_id}/report",response_class=PlainTextResponse)
def get_report(project_id:str):
    path=WORKSPACES_DIR/project_id/"analysis.md"
    if not path.is_file(): raise HTTPException(409,"Informe todavía no disponible")
    return path.read_text(encoding="utf-8")

@app.get("/api/projects/{project_id}/report.html",response_class=HTMLResponse)
def get_html_report(project_id:str):
    path=WORKSPACES_DIR/project_id/"analysis.html"
    if not path.is_file(): raise HTTPException(409,"Informe HTML todavía no disponible")
    return path.read_text(encoding="utf-8")
