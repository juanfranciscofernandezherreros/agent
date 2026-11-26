import os
import re
import urllib.parse

from app.reports_index import build


def _bundle(root, name, mtime, services=(), title="Grupo <1118>"):
    bundle = root / name
    (bundle / "bug-reports").mkdir(parents=True)
    (bundle / "index.html").write_text(
        "<h1>" + title.replace("<", "&lt;").replace(">", "&gt;") + "</h1>",
        encoding="utf-8",
    )
    for filename in ("analysis.html", "activity.html", "agents.html"):
        (bundle / filename).write_text("x", encoding="utf-8")
    for service in services:
        folder = bundle / "repositories" / service
        folder.mkdir(parents=True)
        for filename in ("analysis.html", "activity.html", "agents.html"):
            (folder / filename).write_text("x", encoding="utf-8")
        (bundle / "bug-reports" / (service + "-abc123.html")).write_text("x", encoding="utf-8")
    os.utime(bundle / "index.html", (mtime, mtime))
    return bundle


def test_root_index_lists_generated_reports_not_bug_findings(tmp_path):
    _bundle(tmp_path, "viejo 2025", 1_000_000, ["svc-a"])
    _bundle(tmp_path, "nuevo-2026", 2_000_000, ["svc-a", "svc-b"])
    (tmp_path / "suelto").mkdir()
    html = build(tmp_path).read_text(encoding="utf-8")

    assert html.index("nuevo-2026/index.html") < html.index("viejo%202025/index.html")
    assert "ÚLTIMO ANÁLISIS" in html and html.count("ÚLTIMO ANÁLISIS") == 1
    assert "Grupo &lt;1118&gt;" in html and "suelto" not in html
    for link in (
        "nuevo-2026/analysis.html",
        "nuevo-2026/activity.html",
        "nuevo-2026/agents.html",
        "nuevo-2026/repositories/svc-b/analysis.html",
        "nuevo-2026/repositories/svc-b/activity.html",
        "nuevo-2026/repositories/svc-b/agents.html",
        "viejo%202025/repositories/svc-a/analysis.html",
    ):
        assert "href='" + link + "'" in html, link

    assert "bug-reports" not in html
    assert "posibles bugs" not in html.lower()
    for href in re.findall(r"href='([^']+)'", html):
        assert (tmp_path / urllib.parse.unquote(href)).is_file(), href
    assert "2 análisis disponibles" in html


def test_empty_folder(tmp_path):
    assert "Todavía no hay ningún análisis" in build(tmp_path / "reports").read_text(encoding="utf-8")
