"""Security agents end-to-end: static scan, LLM triage with tools, quality merge, SARIF and reports."""
import json
from pathlib import Path

from app.agents import AnalysisContext
from app.bug_report import build_bug_report_html
from app.security.engine import scan_repository
from app.security.sarif import to_sarif
from app.security.triage import RepositoryTools, triage_finding
from app.supervisor import default_supervisor

VULNERABLE = (
    "import os\n"
    "from flask import Flask, request\n"
    "app = Flask(__name__)\n"
    "\n"
    "@app.route('/run')\n"
    "def run():\n"
    "    cmd = request.args.get('cmd')\n"
    "    os.system('echo ' + cmd)\n"
    "    return 'ok'\n"
)


class ScriptedLLM:
    """Plays back a fixed list of tool actions (no network)."""
    model, provider = "scripted", "fake"

    def __init__(self, actions):
        self.actions, self.calls = list(actions), []

    def complete_json(self, task, schema, data, max_tokens=3000):
        self.calls.append(data)
        return self.actions.pop(0) if self.actions else {"action": "verdict", "verdict": "needs_review", "reason": "fin"}


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "svc"
    root.mkdir()
    (root / "app.py").write_text(VULNERABLE, encoding="utf-8")
    return root


def test_triage_uses_tools_and_validates_citations(tmp_path):
    root = _repo(tmp_path)
    finding = scan_repository(root)["findings"][0]
    llm = ScriptedLLM([
        {"action": "search", "text": "request.args"},
        {"action": "read_file", "path": "app.py", "start": 5, "end": 9},
        {"action": "verdict", "verdict": "confirmed", "reason": "cmd llega a os.system sin validar",
         "exploit_scenario": "cmd=;id", "fix": "subprocess.run([...]) sin shell",
         "evidence": [{"file": "app.py", "line": 8}, {"file": "app.py", "line": 999}, {"file": "../etc/passwd", "line": 1}]},
    ])
    record = triage_finding(llm, RepositoryTools(root), finding)
    assert record["verdict"] == "confirmed"
    assert record["evidence"] == [{"file": "app.py", "line": 8}]  # invented lines and paths outside the repo are dropped
    assert record["steps"] == ["search 'request.args'", "read_file app.py:5-9"]
    assert "app.py:7:" in llm.calls[1]["observacion"]["search"]
    assert "8: " in llm.calls[2]["observacion"]["read_file"]


def test_confirmed_without_valid_evidence_is_downgraded(tmp_path):
    root = _repo(tmp_path)
    finding = scan_repository(root)["findings"][0]
    llm = ScriptedLLM([{"action": "verdict", "verdict": "confirmed", "reason": "seguro que sí", "evidence": []}])
    assert triage_finding(llm, RepositoryTools(root), finding)["verdict"] == "needs_review"


def test_tools_cannot_escape_the_repository(tmp_path):
    root = _repo(tmp_path)
    (tmp_path / "secret.txt").write_text("top secret", encoding="utf-8")
    tools = RepositoryTools(root)
    assert tools.read_file("../secret.txt").startswith("ERROR")
    assert tools.read_file("/etc/passwd").startswith("ERROR")
    assert "top secret" not in tools.search("top secret")


def test_pipeline_merges_security_findings_into_reports(tmp_path):
    root = _repo(tmp_path)
    llm = ScriptedLLM([{"action": "verdict", "verdict": "confirmed", "reason": "flujo directo",
                        "evidence": [{"file": "app.py", "line": 8}]}])
    context = AnalysisContext(root=root, repository="svc")
    default_supervisor(llm).run(context, only=["security_analysis", "security_triage", "quality_analysis"])
    quality = context.results["quality_analysis"]
    candidate = next(c for c in quality["bug_candidates"] if c["code"] == "SEC-CMDI")
    assert candidate["owasp"]["id"] == "A05:2025" and candidate["cwe"]["id"] == "CWE-78"
    assert candidate["triage"]["verdict"] == "confirmed"
    assert [s["kind"] for s in candidate["trace"]] == ["source", "sink"]  # same-line propagation is folded
    assert quality["summary"]["security_findings"] == 1
    html = build_bug_report_html("svc", "grupo", quality)
    assert "Flujo de datos" in html and "OWASP A05:2025" in html and "Confirmado por el agente" in html


def test_false_positive_verdict_moves_finding_out_of_bug_list(tmp_path):
    root = _repo(tmp_path)
    llm = ScriptedLLM([{"action": "verdict", "verdict": "false_positive", "reason": "solo en desarrollo",
                        "evidence": [{"file": "app.py", "line": 8}]}])
    context = AnalysisContext(root=root, repository="svc")
    default_supervisor(llm).run(context, only=["security_analysis", "security_triage", "quality_analysis"])
    quality = context.results["quality_analysis"]
    assert not any(c["code"] == "SEC-CMDI" for c in quality["bug_candidates"])
    assert quality["dismissed_candidates"][0]["code"] == "SEC-CMDI"


def test_without_llm_the_static_findings_still_reach_the_report(tmp_path):
    context = AnalysisContext(root=_repo(tmp_path), repository="svc")
    default_supervisor().run(context, only=["security_analysis", "security_triage", "quality_analysis"])
    assert any(c["code"] == "SEC-CMDI" for c in context.results["quality_analysis"]["bug_candidates"])


def test_sarif_export_is_valid_2_1_0_with_code_flows(tmp_path):
    scan = scan_repository(_repo(tmp_path))
    sarif = json.loads(json.dumps(to_sarif(scan, "7.0.0")))
    run = sarif["runs"][0]
    assert sarif["version"] == "2.1.0"
    rule = run["tool"]["driver"]["rules"][0]
    assert rule["id"] == "SEC-CMDI" and "external/cwe/cwe-78" in rule["properties"]["tags"]
    assert "owasp-top10-2025/A05" in rule["properties"]["tags"]
    result = run["results"][0]
    assert result["level"] == "error" and result["locations"][0]["physicalLocation"]["region"]["startLine"] == 8
    flow = result["codeFlows"][0]["threadFlows"][0]["locations"]
    assert [loc["location"]["physicalLocation"]["region"]["startLine"] for loc in flow] == [7, 8]
    assert result["partialFingerprints"]["minagent/v1"]
