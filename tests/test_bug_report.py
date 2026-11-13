from app.bug_report import build_bug_report_html, build_bug_reports_index


def test_bug_report_contains_service_findings_and_escapes_evidence():
    quality = {
        "score": 74,
        "rating": "Mejorable",
        "summary": {"bug_candidates": 2},
        "bug_candidates": [
            {
                "code": "BUG004", "severity": "high", "title": "Uso de assert",
                "file": "src/Worker.java", "line": 42,
                "excerpt": "assert id != null <script>",
                "description": "Revisar validación", "confidence": "heuristic_candidate",
            },
            {
                "code": "BUG003", "severity": "medium", "title": "TODO pendiente",
                "file": "src/Other.java", "line": 9, "excerpt": "// TODO",
                "description": "Deuda técnica", "confidence": "heuristic_candidate",
            },
        ],
    }
    report = build_bug_report_html("inventory-service", "platform", quality)
    assert "inventory-service" in report
    assert "Uso de assert" in report
    assert "Sustituir assert por una validación explícita" in report
    assert "src/Worker.java" in report
    assert "&lt;script&gt;" in report
    assert "<script>" not in report


def test_bug_report_index_links_only_services_with_candidates():
    index = build_bug_reports_index("platform", [
        {"repository": "inventory-service", "file": "001-inventory-service.html", "count": 2}
    ])
    assert "inventory-service" in index
    assert "001-inventory-service.html" in index
    assert "2 posibles bugs" in index

def test_bug_report_includes_selection_and_export_controls():
    quality = {
        "bug_candidates": [
            {"code": "BUG003", "severity": "medium", "title": "TODO pendiente",
             "file": "src/A.java", "line": 12, "excerpt": "// TODO",
             "description": "Deuda técnica"}
        ]
    }
    report = build_bug_report_html("service-a", "platform", quality, "service-a")
    assert 'class="bug-select" type="checkbox" value="0"' in report
    assert "select-all-bugs" in report
    assert "export-selected-bugs" in report
    assert "/bug-reports/export" in report


def test_consolidated_export_html_escapes_untrusted_finding_text():
    from app.bug_report import build_bug_export_html

    export_data = {
        "group_name": "platform",
        "repository": "service-a",
        "generated_at": "2026-11-13T10:00:00+00:00",
        "tasks": [{
            "id": "service-a-1", "title": "<script>alert(1)</script>",
            "file": "src/A.java", "line": 12, "severity": "high",
            "recommended_action": "Revisar <b>entrada</b>",
        }],
        "bugs": [{
            "code": "BUG006", "title": "Secreto literal",
            "description": "Posible secreto", "excerpt": "token = '<secret>'",
        }],
    }
    report = build_bug_export_html(export_data)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report
    assert "&lt;b&gt;entrada&lt;/b&gt;" in report
    assert "<script>alert(1)</script>" not in report
    assert "Secreto literal" in report

