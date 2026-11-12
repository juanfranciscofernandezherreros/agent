from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, HTMLResponse
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

from .config import APP_NAME, APP_VERSION, WORKSPACES_DIR
from .database import init_db, connect
from .schemas import ProjectCreate
from .engines import clone_repository, analyze_repository
from .deep_analysis import analyze_repository_deep, build_analysis_markdown
from .functional_analysis import analyze_functional_behavior, build_analysis_html

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Análisis estático profundo de microservicios. No genera ni ejecuta código."
)

@app.on_event("startup")
def startup():
    init_db()

def now():
    return datetime.now(timezone.utc).isoformat()

def run_analysis(project_id: str):
    with connect() as con:
        row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            return
        con.execute("UPDATE projects SET status='CLONING',last_error=NULL WHERE id=?", (project_id,))
        git_url, name = row["git_url"], row["name"]
    try:
        source = clone_repository(project_id, git_url)
        with connect() as con:
            con.execute("UPDATE projects SET status='ANALYZING' WHERE id=?", (project_id,))
        inventory = analyze_repository(source)
        deep = analyze_repository_deep(source, inventory)
        functional = analyze_functional_behavior(source)
        analysis = {
            "analysis_version": "3.0",
            "functional_analysis": functional,
            "project_name": name,
            "source_path": str(source),
            "repository_inventory": inventory,
            "deep_analysis": deep,
            "completion_status": "STATIC_ANALYSIS_COMPLETED",
            "runtime_validation": "NOT_PERFORMED"
        }
        folder = WORKSPACES_DIR / project_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
        report = build_analysis_markdown(name, inventory, deep)
        (folder / "analysis.md").write_text(report, encoding="utf-8")
        html_report = build_analysis_html(name, analysis)
        (folder / "analysis.html").write_text(html_report, encoding="utf-8")
        with connect() as con:
            con.execute(
                "UPDATE projects SET status='ANALYSIS_COMPLETED',source_path=?,analysis_json=?,reconstruction_json=NULL,last_error=NULL WHERE id=?",
                (str(source), json.dumps(analysis, ensure_ascii=False), project_id)
            )
    except Exception as exc:
        with connect() as con:
            con.execute("UPDATE projects SET status='FAILED',last_error=? WHERE id=?", (str(exc), project_id))

@app.get("/")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "mode": "analysis_only",
        "message": "Usa POST /api/projects para analizar un repositorio Git HTTPS.",
        "documentation": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION, "mode": "analysis_only"}

@app.post("/api/projects", status_code=202)
def create_project(payload: ProjectCreate, background_tasks: BackgroundTasks):
    project_id = str(uuid.uuid4())
    with connect() as con:
        con.execute(
            "INSERT INTO projects(id,name,git_url,status,created_at) VALUES(?,?,?,?,?)",
            (project_id, payload.name, payload.git_url, "QUEUED", now())
        )
    background_tasks.add_task(run_analysis, project_id)
    return {"project_id": project_id, "status": "QUEUED", "message": "Clonado y análisis estático profundo iniciados."}

@app.get("/api/projects")
def list_projects():
    with connect() as con:
        rows = con.execute(
            "SELECT id,name,status,created_at,last_error FROM projects ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    with connect() as con:
        row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Proyecto no encontrado")
    result = dict(row)
    if result.get("analysis_json"):
        result["analysis"] = json.loads(result.pop("analysis_json"))
    result.pop("reconstruction_json", None)
    return result

@app.get("/api/projects/{project_id}/analysis")
def get_analysis(project_id: str):
    with connect() as con:
        row = con.execute("SELECT status,analysis_json,last_error FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Proyecto no encontrado")
    if row["status"] != "ANALYSIS_COMPLETED" or not row["analysis_json"]:
        return {"project_id": project_id, "status": row["status"], "error": row["last_error"]}
    return json.loads(row["analysis_json"])

@app.get("/api/projects/{project_id}/report", response_class=PlainTextResponse)
def get_report(project_id: str):
    report_path = WORKSPACES_DIR / project_id / "analysis.md"
    if not report_path.is_file():
        with connect() as con:
            row = con.execute("SELECT status,last_error FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Proyecto no encontrado")
        raise HTTPException(409, "El informe todavía no está disponible. Estado: " + row["status"])
    return report_path.read_text(encoding="utf-8")


@app.get("/api/projects/{project_id}/report.html", response_class=HTMLResponse)
def get_html_report(project_id: str):
    report_path = WORKSPACES_DIR / project_id / "analysis.html"
    if not report_path.is_file():
        with connect() as con:
            row = con.execute("SELECT status,last_error FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Proyecto no encontrado")
        raise HTTPException(409, "El informe HTML todavía no está disponible. Estado: " + row["status"])
    return report_path.read_text(encoding="utf-8")
