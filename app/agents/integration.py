from ..communication.contracts import Evidence
from ..integration_analysis import correlate
from .context import AnalysisContext, AnalyzerAgent


class IntegrationAnalysisAgent(AnalyzerAgent):
    name = "integration_analysis"
    scope = "group"

    def run(self, context: AnalysisContext) -> dict:
        result = correlate(context.data["repositories"])
        context.results[self.name] = result
        return result

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        return [Evidence(
            source_agent=self.name, kind="topic_" + str(e.get("role", "unknown")),
            repository=e.get("repository"), file=e.get("file"), line=e.get("line"),
            excerpt=str(e.get("evidence", "")), confidence="heuristic_candidate",
            ref=f"topic:{t['topic']}",
        ).to_dict() for t in result.get("topic_candidates", []) for e in t.get("evidence", [])]
