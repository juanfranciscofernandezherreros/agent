from ..deep_analysis import analyze_repository_deep
from .context import AnalysisContext, AnalyzerAgent


class DeepAnalysisAgent(AnalyzerAgent):
    name = "deep_analysis"

    def run(self, context: AnalysisContext) -> dict:
        result = analyze_repository_deep(context.root, context.results["inventory"])
        context.results[self.name] = result
        return result
