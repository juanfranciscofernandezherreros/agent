from pathlib import Path

import pytest

from app.bug_hunter_exploration import read_repository_file, search_repository, find_symbol


def test_read_file_and_search_are_repo_scoped(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sample.py").write_text("def target():\n    return 1\n", encoding="utf-8")
    result = read_repository_file(tmp_path, "src/sample.py")
    assert "def target" in result["content"]
    assert search_repository(tmp_path, "target")[0]["line"] == 1
    assert find_symbol(tmp_path, "target")[0]["path"] == "src/sample.py"


def test_read_file_rejects_path_traversal(tmp_path: Path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    with pytest.raises(ValueError):
        read_repository_file(tmp_path, "../outside.txt")


def test_read_file_rejects_large_files(tmp_path: Path):
    (tmp_path / "large.txt").write_bytes(b"x" * 20)
    with pytest.raises(ValueError):
        read_repository_file(tmp_path, "large.txt", max_bytes=10)


def test_search_skips_excluded_directories(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "noise.js").write_text("needle", encoding="utf-8")
    assert search_repository(tmp_path, "needle") == []
