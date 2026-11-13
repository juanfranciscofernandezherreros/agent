"""Índice raíz de la carpeta de informes: enlaza todos los análisis descargados y sus documentos.

Uso:  python -m app.reports_index <carpeta_de_informes>
Genera <carpeta>/index.html con enlaces relativos, por lo que funciona sin conexión.
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

GLOBAL_DOCS = (("index.html", "Índice del análisis"), ("analysis.html", "Informe global"),
               ("activity.html", "Histórico de Git"), ("agents.html", "Informe multiagente"),
               ("bug-reports/index.html", "Posibles bugs"))
SERVICE_DOCS = (("analysis.html", "Ficha técnica"), ("activity.html", "Histórico de Git"), ("agents.html", "Informe multiagente"))


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _href(*parts: str) -> str:
    return "/".join(quote(p) for part in parts for p in part.split("/"))


def _title(bundle: Path) -> str:
    """Nombre del grupo tal como aparece en el índice del análisis; si no, el nombre de la carpeta."""
    try:
        match = re.search(r"<h1>(.*?)</h1>", (bundle / "index.html").read_text(encoding="utf-8", errors="replace")[:20000], re.S)
        if match:
            return html.unescape(match.group(1)).strip() or bundle.name
    except OSError:
        pass
    return bundle.name


def scan(report_dir: Path) -> list[dict]:
    bundles = []
    for bundle in report_dir.iterdir():
        if not bundle.is_dir() or not (bundle / "index.html").is_file():
            continue
        services = []
        repos = bundle / "repositories"
        if repos.is_dir():
            for service in sorted(p for p in repos.iterdir() if p.is_dir()):
                docs = [(f, label) for f, label in SERVICE_DOCS if (service / f).is_file()]
                if docs:
                    services.append({"name": service.name, "docs": docs})
        bugs = bundle / "bug-reports"
        bug_files = sorted(p.name for p in bugs.glob("*.html") if p.name != "index.html") if bugs.is_dir() else []
        bundles.append({"folder": bundle.name, "title": _title(bundle), "modified": (bundle / "index.html").stat().st_mtime,
                        "docs": [(f, label) for f, label in GLOBAL_DOCS if (bundle / f).is_file()],
                        "services": services, "bug_files": bug_files})
    return sorted(bundles, key=lambda b: (-b["modified"], b["folder"]))


def render(bundles: list[dict]) -> str:
    cards = []
    for position, b in enumerate(bundles):
        when = datetime.fromtimestamp(b["modified"]).strftime("%d/%m/%Y %H:%M")
        links = "".join("<a href='" + _href(b["folder"], f) + "'>" + _e(label) + "</a>" for f, label in b["docs"])
        rows = []
        for s in b["services"]:
            bug = next((f for f in b["bug_files"] if re.fullmatch(re.escape(s["name"]) + r"-[0-9a-f]{6}\.html", f)
                        or re.fullmatch(r"\d{3}-" + re.escape(s["name"]) + r"\.html", f)), None)
            cells = "".join("<a href='" + _href(b["folder"], "repositories", s["name"], f) + "'>" + _e(label) + "</a>" for f, label in s["docs"])
            if bug:
                cells += "<a href='" + _href(b["folder"], "bug-reports", bug) + "'>Posibles bugs</a>"
            rows.append("<tr><td><b>" + _e(s["name"]) + "</b></td><td class='links'>" + cells + "</td></tr>")
        detail = ("<details" + (" open" if position == 0 else "") + "><summary>" + str(len(b["services"])) + " microservicios</summary>"
                  "<table><tbody>" + "".join(rows) + "</tbody></table></details>") if rows else "<p class='muted'>Sin documentos por microservicio.</p>"
        cards.append("<section" + (" class='latest'" if position == 0 else "") + "><p class='tag'>" + ("ÚLTIMO ANÁLISIS · " if position == 0 else "") + _e(when) +
                     "</p><h2><a href='" + _href(b["folder"], "index.html") + "'>" + _e(b["title"]) + "</a></h2><p class='muted'>" + _e(b["folder"]) +
                     "</p><div class='links main'>" + links + "</div>" + detail + "</section>")
    body = "".join(cards) or "<section><p>Todavía no hay ningún análisis descargado en esta carpeta.</p></section>"
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Documentación de análisis</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fb;color:#17243a;font:15px/1.55 system-ui}header{background:linear-gradient(120deg,#102344,#1e477f,#087e83);color:white;padding:34px max(20px,calc((100% - 1100px)/2))}h1{margin:0 0 6px}main{max-width:1100px;margin:24px auto;padding:0 18px}section{background:white;border:1px solid #dce4ef;border-radius:12px;padding:18px 20px;margin:14px 0}section.latest{border-color:#1e7f83;border-width:2px}h2{margin:2px 0;font-size:1.2rem;overflow-wrap:anywhere}a{color:#2457a6;font-weight:700;text-decoration:none}a:hover{text-decoration:underline}.tag{margin:0;font-size:.8rem;letter-spacing:.04em;color:#1e7f83;font-weight:700}.muted{color:#66758a;margin:2px 0 10px;overflow-wrap:anywhere}.links{display:flex;gap:8px 14px;flex-wrap:wrap}.links.main a{padding:8px 12px;border:1px solid #dce4ef;border-radius:8px}details{margin-top:12px}summary{cursor:pointer;font-weight:700}table{border-collapse:collapse;width:100%;margin-top:8px}td{padding:8px 6px;border-bottom:1px solid #e6ebf2;vertical-align:top;overflow-wrap:anywhere}
</style></head><body><header><p>DOCUMENTACIÓN TÉCNICA</p><h1>Todos los análisis</h1><p>""" + str(len(bundles)) + """ análisis descargados · el más reciente aparece primero</p></header><main>""" + body + """</main></body></html>"""


def build(report_dir) -> Path:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    target = report_dir / "index.html"
    target.write_text(render(scan(report_dir)), encoding="utf-8")
    return target


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m app.reports_index <carpeta_de_informes>")
    print(build(sys.argv[1]))
