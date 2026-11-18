from pathlib import Path

from app.bug_hunter_repository_intelligence import scan_repository


def test_scan_repository_maps_files_without_executing(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('should not execute')", encoding="utf-8")
    (tmp_path / "tests" / "test_main.py").write_text("def test_ok(): pass", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("fastapi", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")

    result = scan_repository(tmp_path)

    assert "src/main.py" in result["entrypoints"]
    assert "tests/test_main.py" in result["test_files"]
    assert "requirements.txt" in result["manifests"]
    assert all("node_modules" not in item["path"] for item in result["file_inventory"])
    assert result["execution_policy"] == "SOURCE_NOT_EXECUTED"
