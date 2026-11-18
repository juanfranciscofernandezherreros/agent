from pathlib import Path

import pytest

from app import local_analysis_cli as cli


class FakeSupervisor:
    def run(self, context, only=None):
        context.results.update({
            "inventory": {"file_count_scanned": 1, "languages": {"Python": 1}, "commit_sha": None},
            "deep_analysis": {
                "scan_stats": {"routes": 0, "python_functions": 0, "python_classes": 0},
                "architecture": {"top_level_directories": [], "entrypoints": [], "deployment_files": []},
                "dependencies": {"manifests": [], "package_json_dependencies": []},
                "api": {"route_candidates": []},
                "data": {"model_candidates": [], "migration_files": []},
                "security": {},
                "integrations": {},
                "configuration": {"environment_variable_names": [], "files": []},
                "tests": {"files": []},
                "limitations": [],
            },
            "functional_analysis": {"summary": {}},
            "java_analysis": {"summary": {}},
            "quality_analysis": {"bug_candidates": [], "summary": {}},
        })


def test_local_analysis_writes_reports_and_does_not_change_source(tmp_path, monkeypatch):
    source = tmp_path / "local-service"
    source.mkdir()
    source_file = source / "service.py"
    source_file.write_text("def run():\n    return 1\n", encoding="utf-8")
    output = tmp_path / "reports"

    monkeypatch.setattr(cli, "default_supervisor", FakeSupervisor)
    monkeypatch.setattr(cli, "build_analysis_markdown", lambda *_: "# mocked report")
    monkeypatch.setattr(cli, "build_analysis_html", lambda *_: "<html>mocked</html>")

    result = cli.analyze_local(source, output, "local-service")

    assert result["completion_status"] == "STATIC_ANALYSIS_COMPLETED"
    assert (output / "analysis.json").is_file()
    assert (output / "analysis.md").is_file()
    assert (output / "analysis.html").is_file()
    assert source_file.read_text(encoding="utf-8") == "def run():\n    return 1\n"


def test_local_analysis_rejects_missing_source(tmp_path):
    with pytest.raises(ValueError, match="no es un directorio"):
        cli.analyze_local(tmp_path / "missing", tmp_path / "out", "missing")



def test_local_analysis_exports_all_bug_candidates_to_json(tmp_path, monkeypatch):
    import json

    source = tmp_path / "service-with-findings"
    source.mkdir()
    (source / "service.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    output = tmp_path / "reports"

    class SupervisorWithFindings:
        def run(self, context, only=None):
            context.results.update({
                "inventory": {"file_count_scanned": 1, "languages": {"Python": 1}},
                "deep_analysis": {"scan_stats": {}, "architecture": {}, "dependencies": {},
                                  "api": {}, "data": {}, "security": {}, "integrations": {},
                                  "configuration": {}, "tests": {"files": []}, "limitations": []},
                "functional_analysis": {"summary": {}},
                "java_analysis": {"summary": {}},
                "quality_analysis": {
                    "bug_candidates": [{"code": "BUG001", "file": "service.py", "line": 1}],
                    "test_bug_candidates": [{"code": "BUG003", "file": "test_service.py", "line": 4}],
                    "summary": {"bug_candidates": 1, "test_bug_groups": 1},
                },
                "llm_bug_hunter": {"findings": [{"title": "LLM candidate"}]},
                "llm_bug_review": {"reviews": [{"verdict": "likely_bug"}]},
            })

    monkeypatch.setattr(cli, "default_supervisor", SupervisorWithFindings)
    monkeypatch.setattr(cli, "build_analysis_markdown", lambda *_: "# report")
    monkeypatch.setattr(cli, "build_analysis_html", lambda *_: "<html></html>")

    cli.analyze_local(source, output, "service-with-findings")

    exported = json.loads((output / "possible-bugs.json").read_text(encoding="utf-8"))
    assert exported["summary"]["total_candidates"] == 2
    assert exported["production_candidates"][0]["code"] == "BUG001"
    assert exported["test_candidates"][0]["code"] == "BUG003"
    assert exported["llm_bug_hunter"]["findings"][0]["title"] == "LLM candidate"
    assert exported["llm_bug_review"]["reviews"][0]["verdict"] == "likely_bug"
