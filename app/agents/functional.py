from ..functional_analysis import analyze_functional_behavior
from .context import AnalysisContext, AnalyzerAgent


class FunctionalAnalysisAgent(AnalyzerAgent):
    name = "functional_analysis"

    def run(self, context: AnalysisContext) -> dict:
        result = analyze_functional_behavior(context.root)
        context.results[self.name] = result
        return result
