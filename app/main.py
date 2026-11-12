from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, HTMLResponse
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

from .config import APP_NAME, APP_VERSION, WORKSPACES_DIR
from .database import init_db, connect
from .schemas import ProjectCreate, AnalysisGroupCreate
from .engines import clone_repository, analyze_repository
from .deep_analysis import analyze_repository_deep, build_analysis_markdown
from .functional_analysis import analyze_functional_behavior, build_analysis_html
from .analysis_orchestrator import run_group_analysis

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
        inventory=analyze_repository(source); deep=analyze_repository_deep(source,inventory)
        functional=analyze_functional_behavior(source)
        from .java_analysis import analyze_java_repository
        java=analyze_java_repository(source)
        analysis={"analysis_version":"5.0","functional_analysis":functional,"project_name":name,
          "source_path":str(source),"repository_inventory":inventory,"deep_analysis":deep,
          "java_analysis":java,"completion_status":"STATIC_ANALYSIS_COMPLETED","runtime_validation":"NOT_PERFORMED"}
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
        analysis=run_group_analysis(group_id,name,repositories)
        status="ANALYSIS_COMPLETED" if not analysis["failures"] else "PARTIAL_ANALYSIS_COMPLETED"
        with connect() as con:
            con.execute("UPDATE analysis_groups SET status=?,analysis_json=?,last_error=NULL WHERE id=?",
              (status,json.dumps(analysis,ensure_ascii=False),group_id))
    except Exception as exc:
        with connect() as con: con.execute("UPDATE analysis_groups SET status='FAILED',last_error=? WHERE id=?",(str(exc),group_id))

@app.get("/")
def root():
    return {"application":APP_NAME,"version":APP_VERSION,"mode":"deep_analysis_orchestrator",
      "message":"Usa /api/projects para un servicio o /api/analysis-groups para varios repositorios relacionados.","documentation":"/docs"}

@app.get("/health")
def health(): return {"status":"ok","version":APP_VERSION,"mode":"deep_analysis_orchestrator"}

@app.post("/api/projects",status_code=202)
def create_project(payload:ProjectCreate,background_tasks:BackgroundTasks):
    project_id=str(uuid.uuid4())
    with connect() as con:
        con.execute("INSERT INTO projects(id,name,git_url,status,created_at) VALUES(?,?,?,?,?)",
          (project_id,payload.name,payload.git_url,"QUEUED",now()))
    background_tasks.add_task(run_analysis,project_id)
    return {"project_id":project_id,"status":"QUEUED","message":"Análisis individual profundo iniciado."}

@app.post("/api/analysis-groups",status_code=202)
def create_analysis_group(payload:AnalysisGroupCreate,background_tasks:BackgroundTasks):
    group_id=str(uuid.uuid4()); repositories=[x.model_dump() for x in payload.repositories]
    with connect() as con:
        con.execute("INSERT INTO analysis_groups(id,name,repositories_json,status,created_at) VALUES(?,?,?,?,?)",
          (group_id,payload.name,json.dumps(repositories,ensure_ascii=False),"QUEUED",now()))
    background_tasks.add_task(run_analysis_group,group_id)
    return {"analysis_group_id":group_id,"status":"QUEUED","repository_count":len(repositories)}

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

@app.get("/api/analysis-groups/{group_id}/analysis")
def get_analysis_group_result(group_id:str):
    with connect() as con: row=con.execute("SELECT status,analysis_json,last_error FROM analysis_groups WHERE id=?",(group_id,)).fetchone()
    if not row: raise HTTPException(404,"Grupo de análisis no encontrado")
    if not row["analysis_json"]: return {"analysis_group_id":group_id,"status":row["status"],"error":row["last_error"]}
    return json.loads(row["analysis_json"])

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
