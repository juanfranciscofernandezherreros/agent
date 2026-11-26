from ..communication.contracts import Evidence
from ..quality_analysis import analyze_quality
from .context import AnalysisContext, AnalyzerAgent


class QualityAnalysisAgent(AnalyzerAgent):
    name = "quality_analysis"
    requires = ("deep_analysis", "functional_analysis", "java_analysis")
    after = ("security_analysis", "security_triage")

    def run(self, context: AnalysisContext) -> dict:
        args = (context.root, context.results["deep_analysis"], context.results["functional_analysis"],
                context.results["java_analysis"])
        scan = context.results.get("security_analysis")
        result = analyze_quality(*args, security_scan=scan) if scan is not None else analyze_quality(*args)
        context.results[self.name] = result
        return result

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        return [Evidence(
            source_agent=self.name, kind="bug_candidate", file=x.get("file"), line=x.get("line"),
            excerpt=x.get("excerpt", ""), confidence="heuristic_candidate",
            ref=f"{x.get('code')}@{x.get('file')}:{x.get('line')}",
        ).to_dict() for x in result.get("bug_candidates", [])]
