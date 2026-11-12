from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from datetime import datetime, timezone
import uuid, json
from .config import APP_NAME, APP_VERSION, WORKSPACES_DIR
from .database import init_db, connect
from .schemas import ProjectCreate, EquivalenceRequest
from .engines import clone_repository, analyze_repository, build_reconstruction_package
from .equivalence import compare_services

app = FastAPI(title=APP_NAME, version=APP_VERSION, description="MVP local de los tres motores")

@app.on_event("startup")
def startup():
    init_db()

def now():
    return datetime.now(timezone.utc).isoformat()

def run_analysis(project_id):
    with connect() as con:
        row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row: return
        con.execute("UPDATE projects SET status='CLONING',last_error=NULL WHERE id=?", (project_id,))
        git_url, name = row["git_url"], row["name"]
    try:
        path = clone_repository(project_id, git_url)
        with connect() as con:
            con.execute("UPDATE projects SET status='ANALYZING' WHERE id=?", (project_id,))
        analysis = analyze_repository(path)
        package = build_reconstruction_package(name, analysis)
        folder = WORKSPACES_DIR / project_id
        (folder/"analysis.json").write_text(json.dumps(analysis,indent=2,ensure_ascii=False),encoding="utf-8")
        (folder/"reconstruction-package.json").write_text(json.dumps(package,indent=2,ensure_ascii=False),encoding="utf-8")
        (folder/"reconstruction-package.md").write_text(
          f"# Paquete de reconstrucción\n\nProyecto: {name}\n\nCommit: {analysis.get('commit_sha')}\n\n"
          f"Lenguajes: {analysis.get('languages')}\n\nRequiere revisión técnica.\n",encoding="utf-8")
        with connect() as con:
            con.execute("UPDATE projects SET status='ANALYSIS_COMPLETED',source_path=?,analysis_json=?,reconstruction_json=? WHERE id=?",
              (str(path),json.dumps(analysis),json.dumps(package),project_id))
    except Exception as exc:
        with connect() as con:
            con.execute("UPDATE projects SET status='FAILED',last_error=? WHERE id=?", (str(exc),project_id))

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse("""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Software Reconstruction Platform</title><style>
body{font-family:system-ui,Segoe UI,sans-serif;max-width:1000px;margin:40px auto;padding:0 18px;background:#f6f7f9;color:#18202a}
.card{background:white;padding:22px;border-radius:14px;margin:16px 0;box-shadow:0 2px 12px #0001}
input,textarea,button{font:inherit;padding:10px;border:1px solid #ccd2da;border-radius:8px;width:100%;box-sizing:border-box;margin:6px 0}
button{background:#172b4d;color:white;cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f3f6;padding:12px;border-radius:8px}
.small{color:#596579;font-size:.92rem}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:700px){.grid{grid-template-columns:1fr}}</style></head><body>
<h1>Software Reconstruction Platform <small>v3.0 MVP</small></h1>
<p class="small">Análisis del repositorio, paquete de reconstrucción y comparación HTTP diferencial.</p>
<div class="card"><h2>1 · Crear proyecto y analizar Git</h2>
<label>Nombre</label><input id="name" placeholder="Mi microservicio"><label>URL Git HTTPS</label>
<input id="git" placeholder="https://github.com/usuario/repositorio.git"><button onclick="createProject()">Clonar y analizar</button><pre id="createOut">Esperando...</pre></div>
<div class="card"><h2>2 · Proyectos</h2><button onclick="loadProjects()">Actualizar</button><pre id="projectsOut">Pulsa actualizar.</pre></div>
<div class="card"><h2>3 · Comparar original y reconstruido</h2>
<p class="small">Introduce URLs base locales. Los casos admiten method, path, headers, params y json.</p>
<div class="grid"><div><label>Original</label><input id="orig" placeholder="http://127.0.0.1:8001"></div>
<div><label>Reconstruido</label><input id="recon" placeholder="http://127.0.0.1:8002"></div></div>
<label>Casos JSON</label><textarea id="cases" rows="7">[
 {"method":"GET","path":"/health"},
 {"method":"GET","path":"/"}
]</textarea><button onclick="compare()">Comparar</button><pre id="compareOut">Esperando...</pre></div>
<script>
async function createProject(){let o=document.getElementById('createOut');o.textContent='Enviando...';
try{let r=await fetch('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('name').value,git_url:document.getElementById('git').value})});o.textContent=JSON.stringify(await r.json(),null,2);loadProjects()}catch(e){o.textContent=String(e)}}
async function loadProjects(){let r=await fetch('/api/projects');document.getElementById('projectsOut').textContent=JSON.stringify(await r.json(),null,2)}
async function compare(){let o=document.getElementById('compareOut');o.textContent='Ejecutando...';try{
let body={original_url:document.getElementById('orig').value,reconstructed_url:document.getElementById('recon').value,cases:JSON.parse(document.getElementById('cases').value)};
let r=await fetch('/api/equivalence/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
loadProjects();
</script></body></html>""")

@app.get("/health")
def health():
    return {"status":"ok","version":APP_VERSION}

@app.post("/api/projects", status_code=202)
def create_project(payload: ProjectCreate, background_tasks: BackgroundTasks):
    project_id = str(uuid.uuid4())
    with connect() as con:
        con.execute("INSERT INTO projects(id,name,git_url,status,created_at) VALUES(?,?,?,?,?)",
          (project_id,payload.name,payload.git_url,"QUEUED",now()))
    background_tasks.add_task(run_analysis,project_id)
    return {"project_id":project_id,"status":"QUEUED","message":"Análisis iniciado."}

@app.get("/api/projects")
def list_projects():
    with connect() as con:
        rows=con.execute("SELECT id,name,status,created_at,last_error FROM projects ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    with connect() as con:
        row=con.execute("SELECT * FROM projects WHERE id=?",(project_id,)).fetchone()
    if not row: raise HTTPException(404,"Proyecto no encontrado")
    d=dict(row)
    for k in ("analysis_json","reconstruction_json"):
        if d.get(k): d[k]=json.loads(d[k])
    return d

@app.get("/api/projects/{project_id}/package")
def get_package(project_id: str):
    with connect() as con:
        row=con.execute("SELECT reconstruction_json FROM projects WHERE id=?",(project_id,)).fetchone()
    if not row: raise HTTPException(404,"Proyecto no encontrado")
    if not row["reconstruction_json"]: raise HTTPException(409,"El análisis no ha terminado")
    return json.loads(row["reconstruction_json"])

@app.post("/api/equivalence/compare")
async def equivalence(payload: EquivalenceRequest):
    result=await compare_services(str(payload.original_url),str(payload.reconstructed_url),payload.cases,payload.timeout_seconds)
    run_id=str(uuid.uuid4())
    with connect() as con:
        con.execute("INSERT INTO equivalence_runs(id,created_at,result_json) VALUES(?,?,?)",
          (run_id,now(),json.dumps(result,ensure_ascii=False)))
    return {"run_id":run_id,**result}

@app.get("/api/equivalence/{run_id}")
def get_equivalence(run_id: str):
    with connect() as con:
        row=con.execute("SELECT result_json FROM equivalence_runs WHERE id=?",(run_id,)).fetchone()
    if not row: raise HTTPException(404,"Ejecución no encontrada")
    return {"run_id":run_id,**json.loads(row["result_json"])}
