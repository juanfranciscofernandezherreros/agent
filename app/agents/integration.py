from ..integration_analysis import correlate
from .context import AnalysisContext, AnalyzerAgent


class IntegrationAnalysisAgent(AnalyzerAgent):
    name = "integration_analysis"
    scope = "group"

    def run(self, context: AnalysisContext) -> dict:
        result = correlate(context.data["repositories"])
        context.results[self.name] = result
        return result
