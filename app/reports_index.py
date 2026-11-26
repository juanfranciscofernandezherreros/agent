"""Índice raíz de los reportes HTML generados, ordenados del más reciente al más antiguo."""
from __future__ import annotations

import html
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from .report_theme import install_stylesheet, stylesheet_link

GLOBAL_DOCS = (
    ("index.html", "Índice de documentación"),
    ("analysis.html", "Informe global"),
    ("activity.html", "Histórico de Git"),
    ("agents.html", "Informe multiagente"),
)
SERVICE_DOCS = (
    ("analysis.html", "Ficha técnica"),
    ("activity.html", "Histórico de Git"),
    ("agents.html", "Informe multiagente"),
)


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _href(*parts: str) -> str:
    return "/".join(quote(p) for part in parts for p in part.split("/"))


def _title(bundle: Path) -> str:
    import re
    try:
        source = (bundle / "index.html").read_text(encoding="utf-8", errors="replace")[:20000]
        match = re.search(r"<h1[^>]*>(.*?)</h1>", source, re.S | re.I)
        if match:
            return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip() or bundle.name
    except OSError:
        pass
    return bundle.name


def scan(report_dir: Path) -> list[dict]:
    bundles = []
    if not report_dir.is_dir():
        return bundles
    for bundle in report_dir.iterdir():
        if not bundle.is_dir() or not (bundle / "index.html").is_file():
            continue
        services = []
        repos = bundle / "repositories"
        if repos.is_dir():
            for service in sorted(p for p in repos.iterdir() if p.is_dir()):
                docs = [(name, label) for name, label in SERVICE_DOCS if (service / name).is_file()]
                if docs:
                    services.append({"name": service.name, "docs": docs})
        docs = [(name, label) for name, label in GLOBAL_DOCS if (bundle / name).is_file()]
        bundles.append({
            "folder": bundle.name,
            "title": _title(bundle),
            "modified": (bundle / "index.html").stat().st_mtime,
            "docs": docs,
            "services": services,
        })
    return sorted(bundles, key=lambda item: (-item["modified"], item["folder"]))


def render(bundles: list[dict]) -> str:
    cards = []
    for position, bundle in enumerate(bundles):
        when = datetime.fromtimestamp(bundle["modified"]).strftime("%d/%m/%Y %H:%M")
        global_links = "".join(
            "<a href='" + _href(bundle["folder"], path) + "'>" + _e(label) + "</a>"
            for path, label in bundle["docs"]
        )
        service_cards = []
        for service in bundle["services"]:
            links = "".join(
                "<a href='" + _href(bundle["folder"], "repositories", service["name"], path) + "'>" + _e(label) + "</a>"
                for path, label in service["docs"]
            )
            service_cards.append(
                "<article class='service'><h3>" + _e(service["name"]) + "</h3>"
                "<div class='links'>" + links + "</div></article>"
            )
        service_section = (
            "<details" + (" open" if position == 0 else "") + "><summary>"
            + str(len(service_cards)) + " microservicios · ver reportes individuales</summary>"
            + "<div class='service-grid'>" + "".join(service_cards) + "</div></details>"
            if service_cards else "<p class='muted'>No hay reportes individuales disponibles.</p>"
        )
        cards.append(
            "<section" + (" class='latest'" if position == 0 else "") + ">"
            "<p class='tag'>" + ("ÚLTIMO ANÁLISIS · " if position == 0 else "") + _e(when) + "</p>"
            "<h2><a href='" + _href(bundle["folder"], "index.html") + "'>" + _e(bundle["title"]) + "</a></h2>"
            "<p class='muted'>" + _e(bundle["folder"]) + "</p>"
            "<h3>Reportes del análisis</h3><div class='links main'>" + global_links + "</div>"
            + service_section + "</section>"
        )
    body = "".join(cards) or "<section><p>Todavía no hay ningún análisis descargado en esta carpeta.</p></section>"
    return """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Índice de reportes generados</title>
""" + stylesheet_link() + """</head><body><header><p>DOCUMENTACIÓN TÉCNICA</p><h1>Índice de reportes generados</h1>
<p>""" + str(len(bundles)) + """ análisis disponibles · el más reciente aparece primero</p></header><main>""" + body + """</main></body></html>"""


def build(report_dir) -> Path:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    target = report_dir / "index.html"
    target.write_text(render(scan(report_dir)), encoding="utf-8")
    install_stylesheet(report_dir)
    return target


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m app.reports_index <carpeta_de_informes>")
    print(build(sys.argv[1]))
