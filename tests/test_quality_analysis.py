from app.quality_analysis import analyze_quality


def test_quality_score_is_bounded_and_exposes_bug_evidence(tmp_path):
    source = tmp_path / "service.py"
    source.write_text("def run():\n    assert user_id\n    # TODO handle retry\n", encoding="utf-8")

    result = analyze_quality(
        tmp_path,
        {"tests": {"files": []}, "parse_issues": [], "security": {}},
        {},
        {},
    )

    assert 0 <= result["score"] <= 100
    assert result["summary"]["bug_candidates"] == 2
    assert {item["code"] for item in result["bug_candidates"]} == {"BUG003", "BUG004"}
    assert all(item["file"] == "service.py" for item in result["bug_candidates"])


def test_quality_score_penalizes_missing_tests_and_static_security_indicators(tmp_path):
    result = analyze_quality(
        tmp_path,
        {"tests": {"files": []}, "parse_issues": [], "security": {"hardcoded_secrets": [{}]}},
        {},
        {},
    )

    assert result["score"] == 87
    assert result["score_factors"]["test_files_detected"] == 0
