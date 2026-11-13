"""Orquestación de un análisis de grupo.

El orquestador solo prepara el entorno (clonado, almacén compartido) y delega en el supervisor:
agentes estáticos -> agentes LLM (opcionales) -> validación cruzada -> agente documental.
"""
import json, uuid
from .config import WORKSPACES_DIR
from . import analysis_cache, engines
from .engines import clone_repository
from .agents import AnalysisContext
from .supervisor import default_supervisor
from .communication import SharedStore
from .group_report import slug, markdown, html_report  # noqa: F401  (compatibilidad)

STATIC_AGENTS=("inventory","deep_analysis","functional_analysis","java_analysis","quality_analysis")


def _require(context, agent, repository=None):
    """Los informes son obligatorios: si el agente documental no terminó, se propaga su error."""
    if agent in context.results:
        return
    message = context.store.get(agent, repository)
    detail = "; ".join(e["message"] for e in message.errors) if message and message.errors else (message.detail if message else "no ejecutado")
    raise RuntimeError(f"El agente {agent} no generó los informes: {detail}")


def _write_progress(folder, state):
    """Estado incremental que consulta el lanzador para la barra de progreso."""
    tmp=folder/"progress.json.tmp"
    tmp.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
    tmp.replace(folder/"progress.json")


def run_group_analysis(group_id,name,repositories,clone_token=None,clone_host=None,supervisor=None):
    folder=WORKSPACES_DIR/group_id; folder.mkdir(parents=True,exist_ok=True)
    results,failures,bug_reports=[],[],[]
    supervisor=supervisor or default_supervisor()
    store=SharedStore(folder/"agent-runs",run_id=group_id)
    shared={"output_dir":folder,"group_name":name,"bug_reports":bug_reports,"group_id":group_id}
    progress={"total":len(repositories),"completed":0,"failed":0,"reused":0,"current":None,"phase":"repositories","items":[]}
    for item in repositories:
        progress["current"]=item["name"]; _write_progress(folder,progress)
        try:
            # Si el repositorio no ha cambiado: no se clona ni se analiza, y sus informes se copian tal cual.
            # Solo se actualiza su histórico de Git.
            commit=engines.remote_head(item["git_url"],clone_token,clone_host) if analysis_cache.enabled() else None
            cached=analysis_cache.load(item,commit)
            if cached:
                context=AnalysisContext(repository=item["name"],store=store,results=cached[0],
                    data={**shared,"repository_input":item,"cached_reports":cached[2]})
                supervisor.run(context,scope="repository",only=["activity_analysis","repository_report"])
            else:
                member_id=str(uuid.uuid4()); source=clone_repository(member_id,item["git_url"],auth_token=clone_token,auth_host=clone_host)
                context=AnalysisContext(root=source,repository=item["name"],store=store,data={**shared,"repository_input":item})
                supervisor.run(context,scope="repository")
            _require(context,"repository_report",item["name"])
            if not cached: analysis_cache.save(item,commit or engines.local_head(source),context.results,folder,context.outputs["static_report_files"])
            entry=context.outputs["repository_entry"]; results.append(entry)
            progress["completed"]+=1; progress["reused"]+=1 if cached else 0
            progress["items"].append({"name":item["name"],"status":"reused" if cached else "done",
                "artifact_dir":entry["artifact_dir"].replace("\\","/"),"bug_report":entry["bug_report"]})
        except Exception as exc:
            failures.append({"repository":item["name"],"error":str(exc)})
            progress["failed"]+=1; progress["items"].append({"name":item["name"],"status":"failed","error":str(exc)[:300]})
        _write_progress(folder,progress)
    if not results: raise RuntimeError("No se pudo analizar ningún repositorio: "+json.dumps(failures,ensure_ascii=False))
    progress["current"]=None; progress["phase"]="global"; _write_progress(folder,progress)
    context=AnalysisContext(store=store,data={**shared,"repositories":results,"failures":failures})
    supervisor.run(context,scope="group")
    _require(context,"group_report")
    result=context.outputs["group_analysis"]
    # El manifiesto definitivo se añade cuando todos los agentes (incluido el documental) han terminado.
    result["agent_runs"]=store.manifest()
    (folder/"analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    progress["phase"]="done"; _write_progress(folder,progress)
    return result
