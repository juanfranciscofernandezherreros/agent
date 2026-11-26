from app.quality_analysis import analyze_quality


def test_detects_sql_injection_candidates_with_security_metadata(tmp_path):
    source = tmp_path / "repository.py"
    source.write_text(
        'query = "SELECT * FROM users WHERE id = " + user_id\n'
        'cursor.execute(query)\n'
        'safe = "SELECT * FROM users WHERE id = ?"\n',
        encoding="utf-8",
    )
    result = analyze_quality(
        tmp_path,
        {"tests": {"files": []}, "parse_issues": [], "security": {}},
        {},
        {},
    )

    finding = next(item for item in result["bug_candidates"] if item["code"] == "SQLI001")
    assert finding["cwe"]["id"] == "CWE-89"
    assert finding["owasp"]["id"] == "A05:2025"
    assert finding["owasp"]["name"] == "Injection"
    assert finding["asvs_area"].startswith("V5")
    assert any("parameterized" in item.lower() for item in finding["owasp_guidance"])
    assert any("SQL_Injection_Prevention_Cheat_Sheet" in url for url in finding["references"])
    assert finding["occurrence_count"] == 1
    assert finding["file"] == "repository.py"
    assert finding["line"] == 1
    assert finding["confidence"] == "heuristic_candidate"
