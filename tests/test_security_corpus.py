"""Benchmark gate: the engine must report exactly the expected findings on the corpus.

Every line annotated with ``expect: RULE[, RULE]`` (or ``expect-next:`` on the previous
line) must produce those rules and no other line may produce any finding. This measures
precision and recall on vulnerable *and* safe code side by side.
"""
import re
from pathlib import Path

import pytest

from app.security.engine import scan_repository
from app.security.java_engine import JAVA_AVAILABLE

CORPUS = Path(__file__).parent / "fixtures" / "security"
EXPECT = re.compile(r"expect(-next)?:\s*([A-Z0-9\-, ]+)")


def _expected(root: Path) -> set:
    expected = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = EXPECT.search(line)
            if match:
                target = number + 1 if match.group(1) else number
                for rule in match.group(2).split(","):
                    if rule.strip():
                        expected.add((rel, target, rule.strip()))
    return expected


def _metrics(root: Path):
    result = scan_repository(root)
    found = {(f["file"], f["line"], f["rule_id"]) for f in result["findings"]}
    expected = _expected(root)
    true_positive = found & expected
    return result, found - expected, expected - found, len(true_positive)


@pytest.mark.parametrize("language", ["python", pytest.param("java", marks=pytest.mark.skipif(
    not JAVA_AVAILABLE, reason="tree-sitter-java no instalado"))])
def test_corpus_has_no_false_positives_or_false_negatives(language):
    result, false_positives, false_negatives, hits = _metrics(CORPUS / language)
    assert hits >= 10
    assert not false_positives, f"Falsos positivos: {sorted(false_positives)}"
    assert not false_negatives, f"Falsos negativos: {sorted(false_negatives)}"
    assert not result["coverage"]["parse_errors"]


def test_findings_carry_owasp_cwe_trace_and_redacted_secrets():
    result = scan_repository(CORPUS / "python")
    sqli = [f for f in result["findings"] if f["rule_id"] == "SEC-SQLI"]
    assert sqli and all(f["owasp"]["id"] == "A05:2025" and f["cwe"]["id"] == "CWE-89" for f in sqli)
    flow = next(f for f in sqli if "run_sql" in f["snippet"])
    kinds = [step["kind"] for step in flow["trace"]]
    assert kinds[0] == "source" and kinds[-1] == "sink"
    assert flow["trace"][-1]["line"] < flow["line"]  # the sink lives inside the helper function
    secrets = [f for f in result["findings"] if f["rule_id"] == "SEC-SECRET"]
    assert secrets and all("Sup3r" not in f["snippet"] and "AKIA" not in f["snippet"] for f in secrets)
    assert result["summary"]["by_owasp"]["A05:2025"] >= 5


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="tree-sitter-java no instalado")
def test_java_flow_crosses_controller_service_and_repository():
    result = scan_repository(CORPUS / "java")
    finding = next(f for f in result["findings"] if f["rule_id"] == "SEC-SQLI" and f["file"].endswith("OrderController.java"))
    files = [step["file"].rsplit("/", 1)[-1] for step in finding["trace"]]
    assert files[0] == "OrderController.java" and files[-1] == "OrderRepository.java"
    assert "OrderService.java" in files
    kafka = next(f for f in result["findings"] if f["file"].endswith("OrderEvents.java"))
    assert kafka["confidence"] == "medium"  # broker messages are external but less directly attacker-controlled


def test_pathological_nesting_is_contained(tmp_path):
    """Untrusted repositories must not be able to crash the scan (CLAUDE.md: adversarial input)."""
    (tmp_path / "deep.py").write_text("x = " + "(" * 3000 + "1" + ")" * 3000 + "\n", encoding="utf-8")
    (tmp_path / "ok.py").write_text("import os\nfrom flask import request\n\n@app.route('/a')\ndef a():\n"
                                    "    os.system(request.args['c'])\n", encoding="utf-8")
    if JAVA_AVAILABLE:
        (tmp_path / "Deep.java").write_text("class Deep { int f() { return " + "(" * 3000 + "1" + ")" * 3000 + "; } }",
                                            encoding="utf-8")
    result = scan_repository(tmp_path)
    assert any(f["rule_id"] == "SEC-CMDI" for f in result["findings"])
    assert any(e["file"] == "deep.py" for e in result["coverage"]["parse_errors"])
