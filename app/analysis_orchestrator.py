"""Orquestación de un análisis de grupo.

El orquestador solo prepara el entorno (clonado, almacén compartido) y delega en el supervisor:
agentes estáticos -> agentes LLM (opcionales) -> validación cruzada -> agente documental.
"""
import json, uuid
from .config import WORKSPACES_DIR
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


def run_group_analysis(group_id,name,repositories,clone_token=None,clone_host=None,supervisor=None):
    folder=WORKSPACES_DIR/group_id; folder.mkdir(parents=True,exist_ok=True)
    results,failures,bug_reports=[],[],[]
    supervisor=supervisor or default_supervisor()
    store=SharedStore(folder/"agent-runs",run_id=group_id)
    shared={"output_dir":folder,"group_name":name,"bug_reports":bug_reports}
    for item in repositories:
        try:
            member_id=str(uuid.uuid4()); source=clone_repository(member_id,item["git_url"],auth_token=clone_token,auth_host=clone_host)
            context=AnalysisContext(root=source,repository=item["name"],store=store,data={**shared,"repository_input":item})
            supervisor.run(context,scope="repository")
            _require(context,"repository_report",item["name"])
            results.append(context.outputs["repository_entry"])
        except Exception as exc: failures.append({"repository":item["name"],"error":str(exc)})
    if not results: raise RuntimeError("No se pudo analizar ningún repositorio: "+json.dumps(failures,ensure_ascii=False))
    context=AnalysisContext(store=store,data={**shared,"repositories":results,"failures":failures})
    supervisor.run(context,scope="group")
    _require(context,"group_report")
    result=context.outputs["group_analysis"]
    # El manifiesto definitivo se añade cuando todos los agentes (incluido el documental) han terminado.
    result["agent_runs"]=store.manifest()
    (folder/"analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    return result
