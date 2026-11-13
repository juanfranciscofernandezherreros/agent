"""Agentes de histórico de actividad (ramas, commits y pushes)."""
import os

from ..activity_analysis import analyze_activity, summarize_group
from ..communication.contracts import AgentSkipped
from .context import AnalysisContext, AnalyzerAgent


class ActivityAnalysisAgent(AnalyzerAgent):
    """Actividad reciente de un repositorio según la API de GitLab."""
    name = "activity_analysis"
    # Se ejecuta cuando el análisis estático del repositorio ha terminado.
    after = ("inventory", "deep_analysis", "functional_analysis", "java_analysis", "quality_analysis")
    optional = True

    def run(self, context: AnalysisContext) -> dict:
        project_id = (context.data.get("repository_input") or {}).get("gitlab_project_id")
        if not project_id:
            raise AgentSkipped("El repositorio no procede de un grupo GitLab: no hay histórico de actividad disponible.")
        if not os.getenv("GITLAB_TOKEN", "").strip():
            raise AgentSkipped("Falta GITLAB_TOKEN para consultar el histórico de actividad.")
        result = analyze_activity(project_id)
        context.results[self.name] = result
        return result


class GroupActivityAgent(AnalyzerAgent):
    """Ranking global: repositorios con más ramas recientes y commits, y usuarios con más pushes."""
    name = "group_activity"
    after = ("integration_analysis",)
    scope = "group"
    optional = True

    def run(self, context: AnalysisContext) -> dict:
        result = summarize_group(context.data.get("repositories", []))
        if not result["repositories_with_data"]:
            raise AgentSkipped("Ningún repositorio tiene histórico de actividad (solo disponible para grupos GitLab).")
        context.results[self.name] = result
        return result
