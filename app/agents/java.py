from ..java_analysis import analyze_java_repository
from .context import AnalysisContext, AnalyzerAgent


class JavaAnalysisAgent(AnalyzerAgent):
    name = "java_analysis"

    def run(self, context: AnalysisContext) -> dict:
        result = analyze_java_repository(context.root)
        context.results[self.name] = result
        return result
