"""The look of every HTML report comes from a single file: app/static/report.css."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from app.agent_report import to_html
from app.bug_report import build_bug_export_html, build_bug_report_html, build_bug_reports_index
from app.documentation import build_documentation_index
from app.functional_analysis import build_analysis_html
from app.group_report import html_report
from app.report_responsive import make_folder_responsive
from app.report_theme import CSS_PATH, apply_report_theme, read_css
from app.reports_index import render
from app.rich_report import build_integral_html

APP_DIR = Path(__file__).resolve().parents[1] / "app"
LINK = "data-agent-report-css"

FINDING = {"code": "BUG001", "severity": "high", "title": "Excepción silenciada", "file": "A.java",
           "line": 4, "description": "catch vacío", "excerpt": "catch(Exception e){}"}
REPO = {
    "name": "orders",
    "artifact_dir": "repositories/orders",
    "java_analysis": {"summary": {"classes": 2, "methods": 3, "sql_statements": 1}},
    "quality_analysis": {"score": 72, "rating": "Aceptable", "summary": {"bug_candidates": 1, "high": 1},
                         "bug_candidates": [FINDING]},
}
ANALYSIS = {
    "repositories": [REPO],
    "bug_reports": [{"repository": "orders", "file": "orders.html", "count": 1}],
    "integration_analysis": {"topic_candidates": [], "shared_contract_candidates": []},
}
EXPORT = {"group_name": "grupo", "repository": "orders", "generated_at": "2026-01-01T00:00:00Z",
          "tasks": [{**FINDING, "id": "orders-1", "repository": "orders", "recommended_action": "Revisar"}],
          "bugs": [{**FINDING, "repository": "orders"}]}

LINKED_REPORTS = {
    "integral": lambda: build_integral_html("grupo", ANALYSIS),
    "functional": lambda: build_analysis_html("orders", {}),
    "documentation_index": lambda: build_documentation_index("grupo", ANALYSIS),
    "bug_report": lambda: build_bug_report_html("orders", "grupo", REPO["quality_analysis"], "orders", "gid", "orders.html"),
    "bug_reports_index": lambda: build_bug_reports_index("grupo", ANALYSIS["bug_reports"], [REPO], "gid"),
    "agent_report": lambda: to_html("Título", "Subtítulo", [{"title": "Sección", "paragraphs": ["texto"],
                                                           "table": (["Estado"], [["COMPLETED"]])}], [("Inicio", "index.html")]),
    "reports_index": lambda: render([]),
    "group_report": lambda: html_report("grupo", ANALYSIS),
}


def _without_scripts(html: str) -> str:
    return re.sub(r"<script\b.*?</script>", "", html, flags=re.S)


def test_stylesheet_is_a_single_light_theme():
    css = read_css()
    assert CSS_PATH.name == "report.css"
    assert "color-scheme: light" in css
    assert "dark" not in css.lower()
    assert "!important" not in css
    assert css.count(":root") == 1
    for selector in (".shell", ".sidebar", ".table-wrap", ".finding", ".task-card", ".severity", "@media (max-width: 900px)", "@media print"):
        assert selector in css


def test_no_generator_declares_its_own_styles():
    offenders = []
    for path in APP_DIR.rglob("*.py"):
        if path.name == "report_theme.py":
            continue
        source = path.read_text(encoding="utf-8")
        for token in ("<style", "style=", ":root{", "color-scheme:"):
            if token in source:
                offenders.append(f"{path.relative_to(APP_DIR)}: {token}")
    assert offenders == []


@pytest.mark.parametrize("name", sorted(LINKED_REPORTS))
def test_every_report_links_the_shared_stylesheet(name):
    html = LINKED_REPORTS[name]()
    assert html.count(LINK) == 1, name
    assert "<style" not in _without_scripts(html), name
    assert 'style="' not in html and "style='" not in html, name


def test_downloadable_export_embeds_the_same_stylesheet():
    html = build_bug_export_html(EXPORT)
    assert '<style id="agent-report-css">' + read_css() + "</style>" in html
    assert LINK not in html


@pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")
@pytest.mark.parametrize("name", ["bug_report", "documentation_index"])
def test_export_scripts_are_valid_javascript(name, tmp_path):
    scripts = re.findall(r"<script>(.*?)</script>", LINKED_REPORTS[name](), flags=re.S)
    assert scripts
    for index, script in enumerate(scripts):
        target = tmp_path / f"{name}-{index}.js"
        target.write_text(script, encoding="utf-8")
        result = subprocess.run(["node", "--check", str(target)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_apply_report_theme_installs_css_and_fixes_relative_links(tmp_path):
    pages = {
        "analysis.html": "report.css",
        "bug-reports/orders.html": "../report.css",
        "repositories/orders/analysis.html": "../../report.css",
    }
    for rel in pages:
        page = tmp_path / rel
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(LINKED_REPORTS["agent_report"](), encoding="utf-8")

    assert make_folder_responsive(tmp_path) == 2  # the root page already had the right href
    assert (tmp_path / "report.css").read_text(encoding="utf-8") == read_css()
    for rel, href in pages.items():
        html = (tmp_path / rel).read_text(encoding="utf-8")
        assert 'href="' + href + '" ' + LINK in html
        assert html.count(LINK) == 1
    assert apply_report_theme(tmp_path) == 0


def test_apply_report_theme_replaces_legacy_inline_themes(tmp_path):
    legacy = ("<html><head><style>:root{color-scheme:dark}</style></head><body><main>x</main>"
              "<style id=\"agent-responsive-layout-v3\">body{}</style></body></html>")
    (tmp_path / "old.html").write_text(legacy, encoding="utf-8")
    apply_report_theme(tmp_path)
    html = (tmp_path / "old.html").read_text(encoding="utf-8")
    assert "<style" not in html
    assert html.count(LINK) == 1
    assert html.index(LINK) < html.index("</head>")


def test_api_serves_stylesheet_for_any_report_path():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    for url in ("/api/analysis-groups/g1/report.css",
                "/api/analysis-groups/g1/repositories/orders/report.css",
                "/api/analysis-groups/g1/bug-reports/report.css",
                "/api/projects/p1/report.css"):
        response = client.get(url)
        assert response.status_code == 200, url
        assert response.headers["content-type"].startswith("text/css")
        assert response.text == read_css()
