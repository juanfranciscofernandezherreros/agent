from ..quality_analysis import analyze_quality
from .context import AnalysisContext, AnalyzerAgent


class QualityAnalysisAgent(AnalyzerAgent):
    name = "quality_analysis"
    requires = ("deep_analysis", "functional_analysis", "java_analysis")

    def run(self, context: AnalysisContext) -> dict:
        result = analyze_quality(
            context.root,
            context.results["deep_analysis"],
            context.results["functional_analysis"],
            context.results["java_analysis"],
        )
        context.results[self.name] = result
        return result
