"""SARIF 2.1.0 export so findings can be uploaded to GitHub/GitLab code scanning."""
from __future__ import annotations

from .catalog import RULES

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
LEVEL = {"high": "error", "medium": "warning", "low": "note"}
SECURITY_SEVERITY = {"high": "8.0", "medium": "5.5", "low": "3.0"}


def _location(file: str, line: int, message: str | None = None) -> dict:
    location = {"physicalLocation": {"artifactLocation": {"uri": file, "uriBaseId": "%SRCROOT%"},
                                     "region": {"startLine": max(1, int(line or 1))}}}
    if message:
        location["message"] = {"text": message}
    return location


def to_sarif(scan: dict, tool_version: str, include_tests: bool = False) -> dict:
    findings = [f for f in scan.get("findings", []) if include_tests or not f.get("is_test")]
    used = sorted({f["rule_id"] for f in findings})
    rules = []
    for rule_id in used:
        rule = RULES[rule_id]
        tags = [rule.category, f"external/cwe/cwe-{rule.cwe[0]}"]
        if rule.owasp:
            tags.append(f"owasp-top10-2025/{rule.owasp}")
        rules.append({
            "id": rule.id,
            "name": rule.id.replace("-", ""),
            "shortDescription": {"text": rule.title},
            "fullDescription": {"text": rule.description},
            "help": {"text": rule.remediation, "markdown": rule.remediation + "".join(f"\n- {r}" for r in rule.references)},
            "helpUri": rule.references[0] if rule.references else f"https://cwe.mitre.org/data/definitions/{rule.cwe[0]}.html",
            "defaultConfiguration": {"level": LEVEL[rule.severity]},
            "properties": {"tags": tags, "precision": "high" if rule.kind == "taint" else "medium",
                           **({"security-severity": SECURITY_SEVERITY[rule.severity]} if rule.category == "security" else {})},
        })
    index = {rule_id: i for i, rule_id in enumerate(used)}
    results = []
    for f in findings:
        result = {
            "ruleId": f["rule_id"],
            "ruleIndex": index[f["rule_id"]],
            "level": LEVEL.get(f["severity"], "warning"),
            "message": {"text": f["message"]},
            "locations": [_location(f["file"], f["line"])],
            "partialFingerprints": {"minagent/v1": f["fingerprint"]},
            "properties": {"confidence": f["confidence"], "severity": f["severity"]},
        }
        if f.get("trace"):
            result["codeFlows"] = [{"threadFlows": [{"locations": [
                {"location": _location(step["file"], step["line"], f"{step['kind']}: {step['note'] or step['code']}")}
                for step in f["trace"]]}]}]
        triage = f.get("triage")
        if triage:
            result["properties"]["triage"] = triage.get("verdict")
            if triage.get("verdict") == "false_positive":
                result["suppressions"] = [{"kind": "external", "justification": triage.get("reason", "")[:500]}]
        results.append(result)
    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "MiniAgent", "version": tool_version, "informationUri":
                                "https://github.com/juanfranciscofernandezherreros/agent", "rules": rules}},
            "results": results,
            "columnKind": "unicodeCodePoints",
        }],
    }
