from pathlib import Path

from app.agents.bug_hunter import BugHunterAgent
from app.agents.context import AnalysisContext


class FakeLLM:
    model = "test-model"
    provider = "test"

    def complete_json(self, *_args, **_kwargs):
        return {"findings": [
            {
                "title": "Failure is converted into success",
                "bug_type": "error_handling",
                "severity": "high",
                "description": "The failure path still returns a success result.",
                "execution_scenario": "The dependency throws during processing.",
                "expected_behavior": "The caller receives a failure result.",
                "actual_behavior": "The method reports success.",
                "impact": "The caller may assume work completed when it did not.",
                "confidence": "high",
                "fix_suggestion": "Propagate the failure or return an explicit failure status.",
                "evidence": [{"file": "service.py", "line": 2}],
            },
            {
                "title": "Hallucinated line should be rejected",
                "bug_type": "logic",
                "severity": "medium",
                "description": "Invalid evidence.",
                "execution_scenario": "N/A",
                "expected_behavior": "N/A",
                "actual_behavior": "N/A",
                "impact": "N/A",
                "confidence": "low",
                "fix_suggestion": "N/A",
                "evidence": [{"file": "service.py", "line": 9999}],
            },
        ]}


def test_bug_hunter_adds_only_findings_with_verified_file_and_line(tmp_path: Path):
    source = tmp_path / "service.py"
    source.write_text("def process():\n    return False\n", encoding="utf-8")
    quality = {"bug_candidates": [], "summary": {"bug_candidates": 0, "high": 0, "medium": 0}}
    context = AnalysisContext(
        root=tmp_path,
        repository="sample",
        results={
            "quality_analysis": quality,
            "deep_analysis": {},
            "functional_analysis": {"summary": {}, "operations": []},
            "java_analysis": {"summary": {}, "methods": [], "classes": []},
            "integration_analysis": {},
        },
    )

    result = BugHunterAgent(FakeLLM()).run(context)

    assert result["summary"]["findings_generated"] == 1
    assert result["summary"]["added_to_bug_report"] == 1
    finding = quality["bug_candidates"][0]
    assert finding["code"] == "BH001"
    assert finding["bug_type"] == "error_handling"
    assert finding["file"] == "service.py"
    assert finding["line"] == 2
    assert finding["evidence"][0]["excerpt"] == "return False"
    assert "Escenario:" in finding["description"]
    assert context.results["llm_bug_hunter"] is result
    assert quality["summary"]["bug_candidates"] == 1
    assert quality["summary"]["high"] == 1
