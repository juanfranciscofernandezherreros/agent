"""Versioned contracts for security/correctness findings produced by the static engines."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

from .catalog import rule as get_rule

SCHEMA_VERSION = "1.0"
CONFIDENCE = ("high", "medium", "low")
TRIAGE_VERDICTS = ("confirmed", "false_positive", "needs_review")


@dataclass
class TraceStep:
    """One hop of a data flow: where untrusted data enters, moves, is cleaned or is used."""
    kind: str  # source | propagation | sanitizer | sink
    file: str
    line: int
    code: str
    note: str = ""


@dataclass
class SecurityFinding:
    rule_id: str
    file: str
    line: int
    snippet: str
    message: str
    language: str
    confidence: str = "medium"
    column: int = 0
    trace: list[TraceStep] = field(default_factory=list)
    severity: str | None = None  # overrides the rule default when set
    is_test: bool = False
    engine: str = "minagent-static"
    triage: dict | None = None

    def __post_init__(self):
        if self.confidence not in CONFIDENCE:
            raise ValueError(f"confianza no válida: {self.confidence}")
        self.snippet = (self.snippet or "").strip()[:300]

    @property
    def rule(self):
        return get_rule(self.rule_id)

    @property
    def fingerprint(self) -> str:
        """Stable across runs and line shifts: rule + file + normalised sink code."""
        code = re.sub(r"\s+", " ", self.snippet)
        return hashlib.sha1(f"{self.rule_id}|{self.file}|{code}".encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        meta = self.rule.metadata()
        data = {
            "schema_version": SCHEMA_VERSION,
            "fingerprint": self.fingerprint,
            **meta,
            "severity": self.severity or meta["severity"],
            "confidence": self.confidence,
            "file": self.file, "line": self.line, "column": self.column,
            "snippet": self.snippet, "message": self.message, "language": self.language,
            "is_test": self.is_test, "engine": self.engine,
            "trace": [asdict(step) for step in self.trace],
        }
        if self.triage:
            data["triage"] = self.triage
        return data


def to_bug_candidate(finding: dict) -> dict:
    """Adapt a finding dict to the legacy ``bug_candidates`` shape used by every report."""
    trace_lines = [
        f"{step['kind']}: {step['file']}:{step['line']} {step['code']}".strip() for step in finding.get("trace", [])
    ]
    occurrence = {"file": finding["file"], "line": finding["line"], "excerpt": finding["snippet"]}
    candidate = {
        "code": finding["rule_id"],
        "severity": finding["severity"],
        "title": finding["title"],
        "description": finding["message"] or finding["description"],
        "confidence": "static_dataflow" if finding.get("trace") else "static_pattern",
        "confidence_level": finding["confidence"],
        "category": finding["category"],
        "cwe": finding["cwe"],
        "references": finding["references"],
        "recommended_action": finding["remediation"],
        "owasp_guidance": [finding["remediation"]],
        "fingerprint": finding["fingerprint"],
        "occurrences": [occurrence],
        "occurrence_count": 1,
        "file": finding["file"], "line": finding["line"], "excerpt": finding["snippet"],
        "trace": finding.get("trace", []),
        "dataflow": trace_lines,
        "source": "security_analysis",
    }
    for key in ("owasp", "asvs_area", "triage"):
        if finding.get(key):
            candidate[key] = finding[key]
    return candidate
