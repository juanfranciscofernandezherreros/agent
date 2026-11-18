from app.quality_analysis import analyze_quality


def test_quality_detects_test_edge_case_patterns(tmp_path):
    source = tmp_path / "edge_cases.py"
    source.write_text(
        "def swallow():\n"
        "    try:\n"
        "        work()\n"
        "    except:\n"
        "        pass\n"
        "def accumulate(items=[]):\n"
        "    items.append(1)\n"
        "    return items\n"
        "value = eval(user_input)\n"
        "if enabled == True:\n"
        "    run()\n"
        "query = 'SELECT * FROM users WHERE id = ' + user_id\n",
        encoding="utf-8",
    )
    result = analyze_quality(
        tmp_path,
        {"tests": {"files": []}, "parse_issues": [], "security": {}},
        {},
        {},
    )
    codes = {item["code"] for item in result["bug_candidates"]}
    assert {"BUG007", "BUG008", "BUG009", "BUG010", "BUG011"} <= codes
    assert all(item["file"] == "edge_cases.py" and item["line"] > 0 for item in result["bug_candidates"])
