"""Cross-linked offline documentation index for a complete group analysis."""
from __future__ import annotations
import html

def _e(value):
    return html.escape(str(value if value is not None else ""), quote=True)

def _validation_label(repo):
    status = (repo.get("agent_insights", {}).get("cross_validation") or {}).get("status")
    return {"CONSISTENT": "Coherente", "WARNINGS": "Con avisos", "CONTRADICTIONS": "Con contradicciones"}.get(status, "Ver informe")

def build_documentation_index(group_name, analysis):
    repos = analysis.get("repositories", [])
    bugs = analysis.get("bug_reports", [])
    bug_by_repo = {item.get("repository"): item for item in bugs}
    rows = []
    for repo in repos:
        artifact = str(repo.get("artifact_dir", "")).replace("\\", "/")
        if not artifact.startswith("repositories/"):
            continue
        bug = bug_by_repo.get(repo.get("name"))
        bug_link = ("<a href='bug-reports/" + _e(bug.get("file")) + "'>Posibles bugs (" + str(bug.get("count", 0)) + ")</a>") if bug else "<span>Sin candidatos detectados</span>"
        quality = repo.get("quality_analysis", {})
        rows.append("<tr><td><b>" + _e(repo.get("name")) + "</b><small>Commit: " + _e(repo.get("inventory", {}).get("commit_sha", "N/D")) + "</small></td><td>" + _e(quality.get("score", "N/D")) + "/100 · " + _e(quality.get("rating", "N/D")) + "</td><td><a href='" + _e(artifact + "/analysis.html") + "'>Ficha técnica</a></td><td><a href='" + _e(artifact + "/agents.html") + "'>" + _e(_validation_label(repo)) + "</a></td><td>" + bug_link + "</td></tr>")
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Índice documental - """ + _e(group_name) + """</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fb;color:#17243a;font:15px/1.55 system-ui}header{background:linear-gradient(120deg,#102344,#1e477f,#087e83);color:white;padding:38px max(20px,calc((100% - 1100px)/2))}main{max-width:1100px;margin:28px auto;padding:0 18px}section{background:white;border:1px solid #dce4ef;border-radius:12px;padding:20px;margin:14px 0}a{color:#2457a6;font-weight:700;text-decoration:none}a:hover{text-decoration:underline}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:11px;border-bottom:1px solid #e6ebf2;vertical-align:top}small{display:block;color:#66758a;margin-top:4px}.actions{display:flex;gap:12px;flex-wrap:wrap}.actions a{padding:10px 14px;border:1px solid #dce4ef;border-radius:8px}@media(max-width:700px){table,tbody,tr,td{display:block}thead{display:none}td{border:0;padding:7px 0}tr{border-bottom:1px solid #e6ebf2;padding:10px 0}}
</style></head><body><header><p>DOCUMENTACIÓN TÉCNICA · """ + _e(analysis.get("completion_status", "STATIC_ANALYSIS_COMPLETED")) + """</p><h1>""" + _e(group_name) + """</h1><p>Índice de navegación de la documentación generada para el conjunto de microservicios.</p><p>""" + str(len(repos)) + """ microservicios · """ + str(len(bugs)) + """ informes de posibles bugs</p></header><main>
<section><h2>Visión global</h2><div class="actions"><a href="analysis.html">Abrir informe global de arquitectura y calidad</a><a href="agents.html">Abrir informe multiagente (LLM y validación cruzada)</a><a href="bug-reports/index.html">Abrir índice de posibles bugs</a></div><p>Empieza por el informe global para entender el contexto y las relaciones. Desde allí puedes abrir cada ficha técnica y cada expediente de posibles bugs.</p></section>
<section><h2>Documentación por microservicio</h2><div style="overflow-x:auto"><table><thead><tr><th>Microservicio</th><th>Calidad estática</th><th>Ficha técnica</th><th>Informe multiagente</th><th>Posibles bugs</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></div></section>
<section><h2>Cómo interpretar los documentos</h2><p>Los informes se basan en análisis estático. Las detecciones de bugs, las puntuaciones y las relaciones entre servicios son indicios que requieren validación. No se han ejecutado los servicios ni sus pruebas.</p></section></main></body></html>"""
