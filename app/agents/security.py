"""Security agents: static taint/pattern analysis and LLM triage with read-only tools."""
from __future__ import annotations

from ..communication.contracts import AgentSkipped, Evidence
from ..llm import LLMError
from ..security.engine import scan_repository
from ..security.triage import VERDICTS, RepositoryTools, triage_finding
from .context import AnalysisContext, AnalyzerAgent
from .llm_agents import LLMAgent

SEVERITY = {"high": 0, "medium": 1, "low": 2}


class SecurityAnalysisAgent(AnalyzerAgent):
    """Source-to-sink taint tracking and structural checks mapped to CWE / OWASP Top 10:2025."""

    name = "security_analysis"
    optional = True  # si el motor falla, el resto del análisis continúa sin estos hallazgos

    def run(self, context: AnalysisContext) -> dict:
        if context.root is None:
            raise AgentSkipped("Sin repositorio local que analizar.")
        result = scan_repository(context.root)
        context.results[self.name] = result
        return result

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        return [Evidence(source_agent=self.name, kind="security_finding", file=f["file"], line=f["line"],
                         excerpt=f["snippet"], confidence="observed_static",
                         ref=f"{f['rule_id']}@{f['file']}:{f['line']}").to_dict()
                for f in result.get("findings", []) if not f.get("is_test")][:500]


class SecurityTriageAgent(LLMAgent):
    """Investigates the most relevant static findings and confirms or discards them."""

    name = "security_triage"
    requires = ("security_analysis",)
    evidence_kind = "security_triage"
    max_findings = 25
    max_steps = 6

    def run(self, context: AnalysisContext) -> dict:
        findings = [f for f in context.results["security_analysis"].get("findings", []) if not f.get("is_test")]
        if not findings:
            raise AgentSkipped("No hay hallazgos de seguridad que revisar.")
        client = self.client()
        chosen = sorted(findings, key=lambda f: (SEVERITY.get(f["severity"], 3), not f.get("trace"),
                                                 f["confidence"] != "high"))[: self.max_findings]
        tools = RepositoryTools(context.root)
        reviews = []
        for finding in chosen:
            try:
                record = triage_finding(client, tools, finding, self.max_steps)
            except LLMError as exc:
                record = {"verdict": "needs_review", "reason": f"Error del LLM: {str(exc)[:300]}", "evidence": [], "steps": []}
            record["fingerprint"] = finding["fingerprint"]
            record["ref"] = f"{finding['rule_id']}@{finding['file']}:{finding['line']}"
            finding["triage"] = {k: v for k, v in record.items() if k not in ("fingerprint", "ref")}
            reviews.append(record)
        counts = {v: sum(r["verdict"] == v for r in reviews) for v in VERDICTS}
        return self.finish(context, client, {
            "reviews": reviews,
            "summary": {"findings_total": len(findings), "reviewed": len(reviews), **counts},
        })

    def cited(self, result):
        out = []
        for review in result.get("reviews", []):
            for item in review.get("evidence", []):
                out.append((f"{review['verdict']}: {review['reason']}", item))
        return out
