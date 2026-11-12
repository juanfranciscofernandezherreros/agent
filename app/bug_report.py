"""Standalone HTML reports for heuristic bug candidates in each repository."""
from __future__ import annotations
import html
from datetime import datetime, timezone

TASKS = {
    "BUG001": "Revisar el bloque de captura y registrar, propagar o tratar explícitamente la excepción.",
    "BUG002": "Revisar la comparación con null/None y confirmar la semántica esperada.",
    "BUG003": "Resolver o documentar la tarea pendiente y añadir una prueba de regresión.",
    "BUG004": "Sustituir assert por una validación explícita que se mantenga activa en producción.",
    "BUG005": "Usar comparación de igualdad en lugar de identidad si se comparan valores.",
    "BUG006": "Eliminar el posible secreto literal, rotarlo si es real y cargarlo desde un gestor seguro.",
}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

def _e(value):
    return html.escape(str(value if value is not None else ""), quote=True)

def _sorted_findings(quality):
    return sorted(list(quality.get("bug_candidates") or []), key=lambda item: (
        SEVERITY_ORDER.get(str(item.get("severity", "low")).lower(), 3),
        str(item.get("file", "")), int(item.get("line") or 0), str(item.get("code", "")),
    ))

def build_bug_report_html(repository, group_name, quality, service_slug=None):
    findings = _sorted_findings(quality)
    summary = quality.get("summary") or {}
    counts = {s: sum(1 for x in findings if str(x.get("severity", "")).lower() == s) for s in ("high", "medium", "low")}
    cards = "".join(
        "<article class='finding " + _e(str(x.get("severity", "low")).lower()) + "'>"
        "<div class='top'><b>" + _e(str(x.get("severity", "low")).upper()) + "</b><span>" + _e(x.get("code", "N/D")) + "</span></div>"
        "<h2>" + _e(x.get("title", "Posible bug")) + "</h2><p>" + _e(x.get("description", "")) + "</p>"
        "<dl><dt>Archivo</dt><dd><code>" + _e(x.get("file", "N/D")) + "</code></dd>"
        "<dt>Línea</dt><dd>" + _e(x.get("line", "N/D")) + "</dd><dt>Confianza</dt><dd>" + _e(x.get("confidence", "heuristic_candidate")) + "</dd></dl>"
        "<h3>Evidencia</h3><pre>" + _e(x.get("excerpt", "")) + "</pre>"
        "<h3>Tarea recomendada</h3><p>" + _e(TASKS.get(x.get("code"), "Revisar el hallazgo y añadir una prueba de regresión.")) + "</p></article>"
        for x in findings
    )
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Posibles bugs - """ + _e(repository) + """</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f6fa;color:#172033;font:15px/1.55 system-ui}
header{background:linear-gradient(120deg,#10254c,#2457c5);color:white;padding:32px max(20px,calc((100% - 1000px)/2))}
main{max-width:1000px;margin:25px auto;padding:0 18px}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:12px}
.metric,.finding,.notice{background:white;border:1px solid #dce3ed;border-radius:12px;padding:16px}.metric strong{display:block;font-size:1.7rem}
.metric span,footer{color:#5b6678}.finding{margin:14px 0;border-left:5px solid #8b96a8}.finding.high{border-left-color:#c43d4b}.finding.medium{border-left-color:#c28a23}.finding.low{border-left-color:#3975bb}
.top{display:flex;gap:12px}.top b{font-size:.8rem;padding:3px 8px;border-radius:20px;background:#edf1f6}.high .top b{background:#fdebed;color:#a62231}.medium .top b{background:#fff3d9;color:#805500}
h1{font-size:clamp(1.6rem,4vw,2.2rem);margin:0}h2{font-size:1.2rem}dl{display:grid;grid-template-columns:100px 1fr;gap:5px 12px}dt{font-weight:650;color:#5b6678}dd{margin:0;overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#111c2e;color:#e8efff;padding:13px;border-radius:8px}.notice{margin:16px 0;color:#5b6678}footer{padding:22px 0;font-size:.85rem}.doc-links{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px}.doc-links a{color:#2457c5;text-decoration:none;border:1px solid #dce3ed;border-radius:7px;padding:7px 10px;font-weight:650}
@media(max-width:520px){header{padding:25px 18px}dl{grid-template-columns:1fr}dd{margin-bottom:7px}}
</style></head><body><header><p>INFORME INDIVIDUAL DE HALLAZGOS</p><h1>""" + _e(repository) + """</h1><p>Conjunto analizado: """ + _e(group_name) + """</p></header><main><nav class="doc-links"><a href="../analysis.html">← Volver al informe global</a>""" + ("<a href='../repositories/" + _e(service_slug) + "/analysis.html'>Abrir ficha técnica del microservicio</a>" if service_slug else "") + """</nav>
<section class="metrics"><div class="metric"><strong>""" + _e(quality.get("score", "N/D")) + """ / 100</strong><span>Calidad estática: """ + _e(quality.get("rating", "Sin puntuación")) + """</span></div>
<div class="metric"><strong>""" + str(len(findings)) + """</strong><span>Posibles bugs</span></div>
<div class="metric"><strong>""" + str(counts["high"]) + """</strong><span>Prioridad alta</span></div>
<div class="metric"><strong>""" + str(counts["medium"]) + """</strong><span>Prioridad media</span></div></section>
<div class="notice"><b>Importante:</b> son candidatos heurísticos, no defectos confirmados. Puede haber falsos positivos y negativos. No se ha ejecutado el servicio ni sus pruebas. Candidatos indicados por el analizador: """ + _e(summary.get("bug_candidates", len(findings))) + """.</div>
<h2>Hallazgos y tareas recomendadas</h2>""" + cards + """<footer>Generado: """ + generated + """ · Revisar cada evidencia y validarla mediante pruebas.</footer></main></body></html>"""

def build_bug_reports_index(group_name, reports):
    rows = "".join("<li><a href='" + _e(x["file"]) + "'>" + _e(x["repository"]) + "</a><span>" + _e(x["count"]) + " posibles bugs</span></li>" for x in reports)
    if not rows:
        rows = "<li>No se detectaron candidatos a posibles bugs en los microservicios analizados.</li>"
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Informes individuales de posibles bugs</title>
<style>body{font:16px/1.5 system-ui;margin:0;background:#f4f6fa;color:#172033}main{max-width:850px;margin:40px auto;padding:0 18px}section{background:white;border:1px solid #dce3ed;border-radius:14px;padding:24px}li{padding:12px 0;border-bottom:1px solid #e5eaf1}a{font-weight:700;color:#2457c5}span{display:block;color:#5b6678;font-size:.9rem}.actions{display:flex;gap:12px;flex-wrap:wrap}.actions a{padding:8px 11px;border:1px solid #dce3ed;border-radius:7px}</style></head><body><main><section><nav class="actions"><a href="../analysis.html">← Informe global</a><a href="../index.html">Índice de documentación</a></nav><h1>Informes individuales de posibles bugs</h1><p>Conjunto analizado: """ + _e(group_name) + """</p><p>Solo aparecen microservicios con uno o más candidatos detectados.</p><ul>""" + rows + """</ul></section></main></body></html>"""
