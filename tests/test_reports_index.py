import os
from app.reports_index import build


def _bundle(root, name, mtime, services=(), title="Grupo <1118>"):
    b = root / name
    (b / "bug-reports").mkdir(parents=True)
    (b / "index.html").write_text("<h1>" + title.replace("<", "&lt;").replace(">", "&gt;") + "</h1>", encoding="utf-8")
    for f in ("analysis.html", "activity.html", "bug-reports/index.html"):
        (b / f).write_text("x", encoding="utf-8")
    for s in services:
        d = b / "repositories" / s
        d.mkdir(parents=True)
        for f in ("analysis.html", "activity.html"):
            (d / f).write_text("x", encoding="utf-8")
        (b / "bug-reports" / (s + "-abc123.html")).write_text("x", encoding="utf-8")
    os.utime(b / "index.html", (mtime, mtime))
    return b


def test_root_index_links_every_bundle_and_document(tmp_path):
    _bundle(tmp_path, "viejo 2025", 1_000_000, ["svc-a"])
    _bundle(tmp_path, "nuevo-2026", 2_000_000, ["svc-a", "svc-b"])
    (tmp_path / "suelto").mkdir()  # carpeta sin índice: se ignora
    html = build(tmp_path).read_text(encoding="utf-8")
    assert html.index("nuevo-2026/index.html") < html.index("viejo%202025/index.html")  # el más reciente primero
    assert "ÚLTIMO ANÁLISIS" in html and html.count("ÚLTIMO ANÁLISIS") == 1
    assert "Grupo &lt;1118&gt;" in html and "suelto" not in html
    for link in ("nuevo-2026/analysis.html", "nuevo-2026/activity.html", "nuevo-2026/bug-reports/index.html",
                 "nuevo-2026/repositories/svc-b/analysis.html", "nuevo-2026/repositories/svc-b/activity.html",
                 "nuevo-2026/bug-reports/svc-b-abc123.html", "viejo%202025/repositories/svc-a/analysis.html"):
        assert "href='" + link + "'" in html, link
    assert "agents.html" not in html  # solo enlaza documentos que existen
    # todos los enlaces apuntan a archivos reales
    import re, urllib.parse
    for href in re.findall(r"href='([^']+)'", html):
        assert (tmp_path / urllib.parse.unquote(href)).is_file(), href
    assert "2 análisis descargados" in html


def test_empty_folder(tmp_path):
    assert "Todavía no hay ningún análisis" in build(tmp_path / "reports").read_text(encoding="utf-8")
