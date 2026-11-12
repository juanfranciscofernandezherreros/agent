from ..communication.contracts import Evidence
from ..java_analysis import analyze_java_repository
from .context import AnalysisContext, AnalyzerAgent


class JavaAnalysisAgent(AnalyzerAgent):
    name = "java_analysis"

    def run(self, context: AnalysisContext) -> dict:
        result = analyze_java_repository(context.root)
        context.results[self.name] = result
        return result

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        out = []
        for key, kind in (("spring_endpoints", "spring_endpoint"), ("kafka_listeners", "kafka_listener"),
                          ("kafka_producers", "kafka_producer"), ("avro_contracts", "contract")):
            for x in result.get(key, []):
                detail = x.get("arguments") or x.get("expression") or x.get("name") or ""
                out.append(Evidence(
                    source_agent=self.name, kind=kind, file=x.get("file"), line=x.get("line"),
                    excerpt=str(detail), confidence="observed_static",
                    ref=f"{kind}@{x.get('file')}:{x.get('line')}",
                ).to_dict())
        return out
