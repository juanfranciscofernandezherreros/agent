from ..engines import analyze_repository
from .context import AnalysisContext, AnalyzerAgent


class InventoryAgent(AnalyzerAgent):
    name = "inventory"

    def run(self, context: AnalysisContext) -> dict:
        result = analyze_repository(context.root)
        context.results[self.name] = result
        return result
