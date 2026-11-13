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

def _bug_export_script():
    return r"""<script>
(function () {
  const checks = Array.from(document.querySelectorAll(".bug-select"));
  const selectAll = document.getElementById("select-all-bugs");
  const button = document.getElementById("export-selected-bugs");
  const status = document.getElementById("export-status");
  if (!button || !checks.length) return;
  if (selectAll) selectAll.addEventListener("change", () => checks.forEach((item) => { item.checked = selectAll.checked; }));
  checks.forEach((item) => item.addEventListener("change", () => {
    if (selectAll) {
      selectAll.checked = checks.every((entry) => entry.checked);
      selectAll.indeterminate = checks.some((entry) => entry.checked) && !selectAll.checked;
    }
  }));
  button.addEventListener("click", async () => {
    const parts = window.location.pathname.split("/");
    const groupId = button.dataset.groupId || parts[3];
    if (!groupId) { status.textContent = "No se pudo identificar el análisis actual."; return; }
    const fallbackReport = button.dataset.report || parts[5];
    const byReport = new Map();
    checks.filter((item) => item.checked).forEach((item) => {
      const reportName = item.dataset.report || fallbackReport;
      if (!reportName || reportName === "index.html") return;
      if (!byReport.has(reportName)) byReport.set(reportName, []);
      byReport.get(reportName).push(Number(item.value));
    });
    const selections = Array.from(byReport, ([report_name, finding_indexes]) => ({ report_name, finding_indexes }));
    if (!selections.length) { status.textContent = "Selecciona al menos un hallazgo."; return; }
    button.disabled = true;
    status.textContent = "Generando los ficheros…";
    try {
      if (window.location.protocol === "file:") {
        status.textContent = "Abre el visor desde la API local (http://127.0.0.1:8001) para habilitar la exportación.";
        return;
      }
      const response = await fetch("/api/analysis-groups/" + encodeURIComponent(groupId) + "/bug-reports/export", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selections })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "No se pudo generar la exportación.");
      const download = (content, type, filename) => {
        const url = URL.createObjectURL(new Blob([content], { type }));
        const anchor = document.createElement("a");
        anchor.href = url; anchor.download = filename; document.body.appendChild(anchor); anchor.click(); anchor.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      };
      download(JSON.stringify(result.json_data, null, 2), "application/json;charset=utf-8", result.json_filename);
      download(result.html_content, "text/html;charset=utf-8", result.html_filename);
      status.textContent = "Exportación completada: JSON y HTML descargados.";
    } catch (error) {
      status.textContent = error.message || "Error de conexión con la API local.";
    } finally { button.disabled = false; }
  });
})();
</script>"""

def build_bug_report_html(repository, group_name, quality, service_slug=None, group_id=None, report_name=None):
    findings = _sorted_findings(quality)
    summary = quality.get("summary") or {}
    counts = {s: sum(1 for x in findings if str(x.get("severity", "")).lower() == s) for s in ("high", "medium", "low")}
    cards = "".join(
        "<article class='finding " + _e(str(x.get("severity", "low")).lower()) + "'>"
        + ("<label class='select-finding'><input class='bug-select' type='checkbox' value='" + str(index) + "' data-report='__REPORT_NAME__'> Seleccionar para exportar</label>" if service_slug else "")
        + "<div class='top'><b>" + _e(str(x.get("severity", "low")).upper()) + "</b><span>" + _e(x.get("code", "N/D")) + "</span></div>"
        + "<h2>" + _e(x.get("title", "Posible bug")) + "</h2><p>" + _e(x.get("description", "")) + "</p>"
        + "<dl><dt>Archivo</dt><dd><code>" + _e(x.get("file", "N/D")) + "</code></dd>"
        + "<dt>Línea</dt><dd>" + _e(x.get("line", "N/D")) + "</dd><dt>Confianza</dt><dd>" + _e(x.get("confidence", "heuristic_candidate")) + "</dd></dl>"
        + "<h3>Evidencia</h3><pre>" + _e(x.get("excerpt", "")) + "</pre>"
        + "<h3>Tarea recomendada</h3><p>" + _e(TASKS.get(x.get("code"), "Revisar el hallazgo y añadir una prueba de regresión.")) + "</p></article>"
        for index, x in enumerate(findings)
    )
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    toolbar = """<section id="export-panel" class="notice export-panel">
<label><input id="select-all-bugs" type="checkbox"> Seleccionar todos</label>
<button id="export-selected-bugs" type="button" data-group-id="__GROUP_ID__" data-report="__REPORT_NAME__">Exportar selección (JSON + HTML)</button>
<span id="export-status" role="status" aria-live="polite">Selecciona uno o varios hallazgos.</span>
</section>"""
    script = _bug_export_script()

    styles = """
.export-panel{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.export-panel button{background:#2457c5;color:white;border:0;border-radius:8px;padding:10px 16px;font-weight:700;cursor:pointer}
.export-panel button:disabled{opacity:.6;cursor:wait}
.select-finding{display:inline-flex;align-items:center;gap:8px;font-weight:650;color:#2457c5;margin-bottom:10px}
"""
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Posibles bugs - """ + _e(repository) + """</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f6fa;color:#172033;font:15px/1.55 system-ui}
header{background:linear-gradient(120deg,#10254c,#2457c5);color:white;padding:32px max(20px,calc((100% - 1000px)/2))}
main{max-width:1000px;margin:25px auto;padding:0 18px}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:12px}
.metric,.finding,.notice{background:white;border:1px solid #dce3ed;border-radius:12px;padding:16px}.metric strong{display:block;font-size:1.7rem}
.metric span,footer{color:#5b6678}.finding{margin:14px 0;border-left:5px solid #8b96a8}.finding.high{border-left-color:#c43d4b}.finding.medium{border-left-color:#c28a23}.finding.low{border-left-color:#3975bb}
.top{display:flex;gap:12px}.top b{font-size:.8rem;padding:3px 8px;border-radius:20px;background:#edf1f6}.high .top b{background:#fdebed;color:#a62231}.medium .top b{background:#fff3d9;color:#805500}
h1{font-size:clamp(1.6rem,4vw,2.2rem);margin:0}h2{font-size:1.2rem}dl{display:grid;grid-template-columns:100px 1fr;gap:5px 12px}dt{font-weight:650;color:#5b6678}dd{margin:0;overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#111c2e;color:#e8efff;padding:13px;border-radius:8px}.notice{margin:16px 0;color:#5b6678}.doc-links{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px}.doc-links a{color:#2457c5;text-decoration:none;border:1px solid #dce3ed;border-radius:7px;padding:7px 10px;font-weight:650}
""" + styles + """
@media(max-width:520px){header{padding:25px 18px}dl{grid-template-columns:1fr}dd{margin-bottom:7px}}
</style></head><body><header><p>INFORME INDIVIDUAL DE HALLAZGOS</p><h1>""" + _e(repository) + """</h1><p>Conjunto analizado: """ + _e(group_name) + """</p></header><main><nav class="doc-links"><a href="../analysis.html">← Volver al informe global</a>""" + ("<a href='../repositories/" + _e(service_slug) + "/analysis.html'>Abrir ficha técnica del microservicio</a>" if service_slug else "") + """</nav>
<section class="metrics"><div class="metric"><strong>""" + _e(quality.get("score", "N/D")) + """ / 100</strong><span>Calidad estática: """ + _e(quality.get("rating", "Sin puntuación")) + """</span></div>
<div class="metric"><strong>""" + str(len(findings)) + """</strong><span>Posibles bugs</span></div>
<div class="metric"><strong>""" + str(counts["high"]) + """</strong><span>Prioridad alta</span></div>
<div class="metric"><strong>""" + str(counts["medium"]) + """</strong><span>Prioridad media</span></div></section>
<div class="notice"><b>Importante:</b> son candidatos heurísticos, no defectos confirmados. Puede haber falsos positivos y negativos. No se ha ejecutado el servicio ni sus pruebas. Candidatos indicados por el analizador: """ + _e(summary.get("bug_candidates", len(findings))) + """.</div>
<h2>Hallazgos y tareas recomendadas</h2>""" + (toolbar.replace("__GROUP_ID__", _e(group_id or "")).replace("__REPORT_NAME__", _e(report_name or "")) if service_slug else "") + (cards.replace("__REPORT_NAME__", _e(report_name or "")) if service_slug else cards) + """<footer>Generado: """ + generated + """ · Revisar cada evidencia y validarla mediante pruebas.</footer></main>""" + (script if service_slug else "") + """</body></html>"""


def build_bug_export_html(export_data):
    """Build a self-contained HTML report from server-validated selected findings."""
    tasks = export_data["tasks"]
    bugs = export_data["bugs"]
    rows = "".join(
        "<tr><td>" + _e(item.get("id")) + "</td><td>" + _e(item.get("repository")) + "</td><td>" + _e(item.get("title")) +
        "</td><td>" + _e(item.get("file")) + ":" + _e(item.get("line")) +
        "</td><td>" + _e(item.get("severity")) + "</td><td>" +
        _e(item.get("recommended_action")) + "</td></tr>"
        for item in tasks
    )
    bug_rows = "".join(
        "<tr><td>" + _e(item.get("repository")) + "</td><td>" + _e(item.get("code")) + "</td><td>" + _e(item.get("title")) +
        "</td><td>" + _e(item.get("description")) + "</td><td>" +
        _e(item.get("excerpt")) + "</td></tr>"
        for item in bugs
    )
    return """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Exportación de tareas y bugs</title>
<style>
body{font:15px/1.5 system-ui;margin:0;background:#f4f6fa;color:#172033}
main{max-width:1100px;margin:32px auto;padding:0 18px}
section{background:white;border:1px solid #dce3ed;border-radius:12px;padding:20px;margin:16px 0}
table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;padding:9px;border-bottom:1px solid #e5eaf1;overflow-wrap:anywhere}
th{background:#edf1f6}h1,h2{color:#172b4d}
@media(max-width:700px){main{overflow-x:auto}table{min-width:650px}}
</style></head><body><main><h1>Informe consolidado de tareas y posibles bugs</h1>
<p>Conjunto: """ + _e(export_data["group_name"]) + """ · Microservicio: """ + _e(export_data["repository"]) + """</p>
<p>Generado: """ + _e(export_data["generated_at"]) + """ · Elementos seleccionados: """ + str(len(tasks)) + """</p>
<section><h2>Tareas pendientes (""" + str(len(tasks)) + """)</h2>
<table><thead><tr><th>ID</th><th>Microservicio</th><th>Hallazgo</th><th>Ubicación</th><th>Severidad</th><th>Acción recomendada</th></tr></thead><tbody>""" + rows + """</tbody></table></section>
<section><h2>Posibles bugs (""" + str(len(bugs)) + """)</h2>
<table><thead><tr><th>Microservicio</th><th>Código</th><th>Título</th><th>Detalle</th><th>Evidencia</th></tr></thead><tbody>""" + bug_rows + """</tbody></table></section>
<p>Los elementos son candidatos heurísticos y deben validarse mediante revisión y pruebas.</p>
</main></body></html>"""

def build_bug_reports_index(group_name, reports, repositories=None, group_id=None):
    rows = "".join(
        "<li><a href='" + _e(x["file"]) + "'>" + _e(x["repository"]) +
        "</a><span>" + _e(x["count"]) + " posibles bugs</span></li>"
        for x in reports
    )
    if not rows:
        rows = "<li>No se detectaron candidatos a posibles bugs en los microservicios analizados.</li>"

    selectable = []
    report_names = {item.get("file") for item in reports}
    for repository in repositories or []:
        bug_report = repository.get("bug_report") or ""
        if not bug_report.startswith("bug-reports/"):
            continue
        report_name = bug_report.split("/", 1)[1]
        if report_name not in report_names:
            continue
        slug = str(repository.get("artifact_dir", "")).split("/")[-1]
        for index, finding in enumerate(_sorted_findings(repository.get("quality_analysis") or {})):
            label = (
                "<label class='finding-choice'><input class='bug-select' type='checkbox' data-report='" +
                _e(report_name) + "' value='" + str(index) + "'><span><b>" +
                _e(str(finding.get("severity", "low")).upper()) + " · " + _e(repository.get("name", "Microservicio")) +
                "</b><br>" + _e(finding.get("title", "Posible bug")) + "<small>" +
                _e(finding.get("file", "N/D")) + ":" + _e(finding.get("line", "N/D")) +
                " · " + _e(TASKS.get(finding.get("code"), "Revisar el hallazgo y añadir una prueba de regresión.")) +
                "</small></span></label>"
            )
            selectable.append(label)
    selection_ui = ""
    if selectable:
        selection_ui = """<section class="selection"><h2>Seleccionar tareas y posibles bugs</h2>
<p>Marca hallazgos de uno o varios microservicios y genera un único informe consolidado.</p>
<div class="selection-actions"><label><input id="select-all-bugs" type="checkbox"> Seleccionar todos</label>
<button id="export-selected-bugs" type="button" data-group-id="__GROUP_ID__">Exportar selección (JSON + HTML)</button>
<span id="export-status" role="status" aria-live="polite">No hay hallazgos seleccionados.</span></div>
<div class="finding-list">""" + "".join(selectable) + """</div></section>"""
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Informes individuales de posibles bugs</title>
<style>
body{font:16px/1.5 system-ui;margin:0;background:#f4f6fa;color:#172033}
main{max-width:950px;margin:40px auto;padding:0 18px}
section{background:white;border:1px solid #dce3ed;border-radius:14px;padding:24px;margin:16px 0}
li{padding:12px 0;border-bottom:1px solid #e5eaf1}
a{font-weight:700;color:#2457c5}span{display:block;color:#5b6678;font-size:.9rem}
.actions,.selection-actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.actions a{padding:8px 11px;border:1px solid #dce3ed;border-radius:7px}
.finding-list{display:grid;gap:8px;margin-top:14px}
.finding-choice{display:flex;gap:12px;align-items:flex-start;padding:12px;border:1px solid #e1e7f0;border-radius:9px;cursor:pointer}
.finding-choice input{margin-top:5px}.finding-choice span{font-size:.95rem;color:#172033}
.finding-choice small{display:block;color:#5b6678;margin-top:3px;overflow-wrap:anywhere}
.selection-actions button{background:#2457c5;color:white;border:0;border-radius:8px;padding:10px 16px;font-weight:700;cursor:pointer}
.selection-actions button:disabled{opacity:.6;cursor:wait}
@media(max-width:520px){main{margin:20px auto}section{padding:16px}}
</style></head><body><main><section><nav class="actions"><a href="../analysis.html">← Informe global</a><a href="../index.html">Índice de documentación</a></nav>
<h1>Informes individuales de posibles bugs</h1><p>Conjunto analizado: """ + _e(group_name) + """</p>
<p>Solo aparecen microservicios con uno o más candidatos detectados. Puedes abrir un informe individual o seleccionar hallazgos de varios servicios para exportarlos juntos.</p><ul>""" + rows + """</ul></section>""" + selection_ui.replace("__GROUP_ID__", _e(group_id or "")) + """</main>""" + (_bug_export_script() if selectable else "") + """</body></html>"""
