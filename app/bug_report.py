"""Standalone HTML reports for heuristic bug candidates in each repository."""
from __future__ import annotations
import html
from datetime import datetime, timezone
import json
from .report_theme import inline_stylesheet, stylesheet_link

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


def _repository_bug_findings(repository):
    """Return production, test and LLM candidates shown across the repository reports."""
    quality = repository.get("quality_analysis") or {}
    findings = []
    findings.extend({**item, "scope": item.get("scope", "production"),
                     "source": item.get("source", "static_quality")}
                    for item in quality.get("bug_candidates") or [])
    findings.extend({**item, "scope": "test", "source": item.get("source", "static_quality")}
                    for item in quality.get("test_bug_candidates") or [])
    llm_findings = ((repository.get("agent_insights") or {}).get("llm_bug_hunter") or {}).get("findings") or []
    findings.extend({**item, "scope": item.get("scope", "production"),
                     "source": "llm_bug_hunter"}
                    for item in llm_findings)
    return _sorted_findings({"bug_candidates": findings})

def _bug_export_script():
    return (r"""<script>
const AGENT_REPORT_CSS = __AGENT_REPORT_CSS__;
(function () {
  const checks = Array.from(document.querySelectorAll(".bug-select"));
  const selectAll = document.getElementById("select-all-bugs");
  const button = document.getElementById("export-selected-bugs");
  const exportAllButton = document.getElementById("export-all-bugs-json");
  const status = document.getElementById("export-status");
  const safeName = (value) => String(value || "hallazgo").normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "").replace(/[^a-zA-Z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "").slice(0, 90) || "hallazgo";
  const makeZip = (files) => {
    const encoder = new TextEncoder();
    const crcTable = new Uint32Array(256);
    for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1); crcTable[n] = c >>> 0; }
    const crc32 = (bytes) => { let c = 0xffffffff; for (const byte of bytes) c = crcTable[(c ^ byte) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
    const u16 = (view, offset, value) => view.setUint16(offset, value, true);
    const u32 = (view, offset, value) => view.setUint32(offset, value >>> 0, true);
    const local = [], central = []; let offset = 0;
    const now = new Date(), dosTime = (now.getHours()<<11)|(now.getMinutes()<<5)|(now.getSeconds()>>1);
    const dosDate = ((Math.max(1980,now.getFullYear())-1980)<<9)|((now.getMonth()+1)<<5)|now.getDate();
    files.forEach((file) => {
      const name = encoder.encode(file.name), data = encoder.encode(file.content), crc = crc32(data);
      const header = new Uint8Array(30 + name.length), hv = new DataView(header.buffer);
      u32(hv,0,0x04034b50); u16(hv,4,20); u16(hv,6,0x0800); u16(hv,8,0);
      u16(hv,10,dosTime); u16(hv,12,dosDate); u32(hv,14,crc); u32(hv,18,data.length); u32(hv,22,data.length); u16(hv,26,name.length); u16(hv,28,0); header.set(name,30);
      local.push(header,data);
      const ch = new Uint8Array(46 + name.length), cv = new DataView(ch.buffer);
      u32(cv,0,0x02014b50); u16(cv,4,20); u16(cv,6,20); u16(cv,8,0x0800); u16(cv,10,0);
      u16(cv,12,dosTime); u16(cv,14,dosDate); u32(cv,16,crc); u32(cv,20,data.length); u32(cv,24,data.length);
      u16(cv,28,name.length); u16(cv,30,0); u16(cv,32,0); u16(cv,34,0); u16(cv,36,0); u32(cv,38,0); u32(cv,42,offset); ch.set(name,46);
      central.push(ch); offset += header.length + data.length;
    });
    const centralSize = central.reduce((sum, part) => sum + part.length, 0);
    const end = new Uint8Array(22), ev = new DataView(end.buffer);
    u32(ev,0,0x06054b50); u16(ev,4,0); u16(ev,6,0); u16(ev,8,files.length); u16(ev,10,files.length);
    u32(ev,12,centralSize); u32(ev,16,offset); u16(ev,20,0);
    return new Blob([...local,...central,end], {type:"application/zip"});
  };
  if (exportAllButton && checks.length) exportAllButton.addEventListener("click", () => {
    try {
      const selected = checks;
      const groupName = exportAllButton.dataset.groupName || "analysis";
      const groupId = exportAllButton.dataset.groupId || "";
      const files = [];
      selected.forEach((item, index) => {
        const finding = JSON.parse(item.dataset.finding || "{}");
        const repository = item.dataset.repository || "microservicio";
        const filename = safeName(repository) + "__" + safeName(finding.code) + "__" +
          safeName(finding.file) + "__L" + safeName(finding.line || index + 1) + "__" + String(index + 1).padStart(4,"0") + ".json";
        const payload = {schema_version:"1.0", analysis_group_id:groupId, group_name:groupName,
          repository, exported_at:new Date().toISOString(), finding};
        files.push({name:"revisao/" + filename, content:JSON.stringify(payload,null,2)});
      });
      if (!files.length) { status.textContent = "No hay bugs para exportar."; return; }
      const manifest = {schema_version:"1.0", group_name:groupName, analysis_group_id:groupId,
        total_findings:files.length, files:files.map(file=>file.name)};
      files.push({name:"revisao/manifest.json",content:JSON.stringify(manifest,null,2)});
      const url = URL.createObjectURL(makeZip(files));
      const anchor = document.createElement("a"); anchor.href=url; anchor.download="revisao.zip";
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      window.setTimeout(()=>URL.revokeObjectURL(url),2000);
      status.textContent = files.length - 1 + " JSON individuales preparados en revisao/ (revisao.zip).";
    } catch (error) { status.textContent = error.message || "No se pudo crear el ZIP."; }
  });
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
      const download = (content, type, filename) => {
        const url = URL.createObjectURL(new Blob([content], { type }));
        const anchor = document.createElement("a");
        anchor.href = url; anchor.download = filename; document.body.appendChild(anchor); anchor.click(); anchor.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      };
      let exportData, htmlContent, jsonFilename, htmlFilename;
      if (window.location.protocol === "file:") {
        // Los informes locales no pueden llamar a la API por las restricciones CORS de file://.
        // Cada checkbox lleva los datos del hallazgo para construir la exportación sin conexión.
        const selected = checks.filter((item) => item.checked);
        const tasks = [], bugs = [];
        selected.forEach((item) => {
          const finding = JSON.parse(item.dataset.finding || "{}");
          const repository = item.dataset.repository || "microservicio";
          const action = finding.recommended_action || "Revisar el hallazgo y añadir una prueba de regresión.";
          const index = Number(item.value);
          const slug = item.dataset.serviceSlug || repository.toLowerCase().replace(/[^a-z0-9]+/g, "-");
          tasks.push({ id: slug + "-" + (index + 1), repository, title: finding.title || "Posible bug",
            description: finding.description || "", status: "Pendiente", severity: finding.severity || "low",
            file: finding.file || "N/D", line: finding.line || "N/D", recommended_action: action });
          bugs.push({ repository, code: finding.code || "N/D", title: finding.title || "Posible bug",
            description: finding.description || "", severity: finding.severity || "low", file: finding.file || "N/D",
            line: finding.line || "N/D", confidence: finding.confidence || "heuristic_candidate",
            excerpt: finding.excerpt || "", recommended_action: action });
        });
        const groupName = button.dataset.groupName || "analysis";
        exportData = { schema_version: "1.0", analysis_group_id: groupId, group_name: groupName,
          repository: Array.from(new Set(tasks.map((item) => item.repository))).sort().join(", "),
          generated_at: new Date().toISOString(), total_tasks: tasks.length, total_bugs: bugs.length, tasks, bugs };
        const esc = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (ch) =>
          ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
        const taskRows = tasks.map((x) => "<tr>" + [x.id,x.repository,x.title,x.file + ":" + x.line,x.severity,x.recommended_action].map((v) => "<td>"+esc(v)+"</td>").join("") + "</tr>").join("");
        const bugRows = bugs.map((x) => "<tr>" + [x.repository,x.code,x.title,x.description,x.excerpt].map((v) => "<td>"+esc(v)+"</td>").join("") + "</tr>").join("");
        htmlContent = "<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Exportación de tareas y bugs</title>" + AGENT_REPORT_CSS + "</head><body><header><p>INFORME DE EXPORTACIÓN</p><h1>Tareas y posibles bugs</h1><p>Conjunto: "+esc(groupName)+" · Microservicios: "+esc(exportData.repository)+"</p></header><main><section><h2>Tareas pendientes</h2><div class='table-wrap'><table><tr><th>ID</th><th>Microservicio</th><th>Hallazgo</th><th>Ubicación</th><th>Severidad</th><th>Acción recomendada</th></tr>"+taskRows+"</table></div></section><section><h2>Posibles bugs</h2><div class='table-wrap'><table><tr><th>Microservicio</th><th>Código</th><th>Título</th><th>Detalle</th><th>Evidencia</th></tr>"+bugRows+"</table></div></section></main></body></html>";
        const safeId = String(groupId).slice(0, 8);
        jsonFilename = "tareas-y-bugs-" + safeId + ".json";
        htmlFilename = "informe-tareas-y-bugs-" + safeId + ".html";
      } else {
        const response = await fetch("/api/analysis-groups/" + encodeURIComponent(groupId) + "/bug-reports/export", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ selections })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "No se pudo generar la exportación.");
        exportData = result.json_data; htmlContent = result.html_content;
        jsonFilename = result.json_filename; htmlFilename = result.html_filename;
      }
      download(JSON.stringify(exportData, null, 2), "application/json;charset=utf-8", jsonFilename);
      download(htmlContent, "text/html;charset=utf-8", htmlFilename);
      status.textContent = "Exportación completada: JSON y HTML descargados.";
    } catch (error) {
      status.textContent = error.message || "Error de conexión con la API local.";
    } finally { button.disabled = false; }
  });
})();
</script>""").replace("__AGENT_REPORT_CSS__", json.dumps(inline_stylesheet()))

def build_bug_report_html(repository, group_name, quality, service_slug=None, group_id=None, report_name=None):
    findings = _sorted_findings(quality)
    summary = quality.get("summary") or {}
    counts = {s: sum(1 for x in findings if str(x.get("severity", "")).lower() == s) for s in ("high", "medium", "low")}
    cards = "".join(
        "<article class='finding " + _e(str(x.get("severity", "low")).lower()) + "'>"
        + ("<label class='select-finding'><input class='bug-select' type='checkbox' value='" + str(index) + "' data-report='__REPORT_NAME__' data-repository='" + _e(repository) + "' data-service-slug='" + _e(service_slug or "") + "' data-finding='" + _e(__import__('json').dumps({**x, "recommended_action": TASKS.get(x.get("code"), x.get("fix_suggestion") or "Revisar el hallazgo y añadir una prueba de regresión.")}, ensure_ascii=False)) + "'> Seleccionar para exportar</label>" if service_slug else "")
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
<button id="export-all-bugs-json" type="button" data-group-id="__GROUP_ID__" data-group-name="__GROUP_NAME__">Exportar todos como JSON individuales (revisao.zip)</button>
<span id="export-status" role="status" aria-live="polite">Selecciona uno o varios hallazgos.</span>
</section>"""
    script = _bug_export_script()

    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Posibles bugs - """ + _e(repository) + """</title>""" + stylesheet_link() + """</head><body><header><p>INFORME INDIVIDUAL DE HALLAZGOS</p><h1>""" + _e(repository) + """</h1><p>Conjunto analizado: """ + _e(group_name) + """</p></header><main><nav class="doc-links"><a href="../analysis.html">← Volver al informe global</a>""" + ("<a href='../repositories/" + _e(service_slug) + "/analysis.html'>Abrir ficha técnica del microservicio</a>" if service_slug else "") + """</nav>
<section class="metrics"><div class="metric"><strong>""" + _e(quality.get("score", "N/D")) + """ / 100</strong><span>Calidad estática: """ + _e(quality.get("rating", "Sin puntuación")) + """</span></div>
<div class="metric"><strong>""" + str(len(findings)) + """</strong><span>Posibles bugs</span></div>
<div class="metric"><strong>""" + str(counts["high"]) + """</strong><span>Prioridad alta</span></div>
<div class="metric"><strong>""" + str(counts["medium"]) + """</strong><span>Prioridad media</span></div></section>
<div class="notice"><b>Importante:</b> son candidatos heurísticos, no defectos confirmados. Puede haber falsos positivos y negativos. No se ha ejecutado el servicio ni sus pruebas. Candidatos indicados por el analizador: """ + _e(summary.get("bug_candidates", len(findings))) + """.</div>
<h2>Hallazgos y tareas recomendadas</h2>""" + (toolbar.replace("__GROUP_ID__", _e(group_id or "")).replace("__REPORT_NAME__", _e(report_name or "")).replace("__GROUP_NAME__", _e(group_name)) if service_slug else "") + (cards.replace("__REPORT_NAME__", _e(report_name or "")) if service_slug else cards) + """<footer>Generado: """ + generated + """ · Revisar cada evidencia y validarla mediante pruebas.</footer></main>""" + (script if service_slug else "") + """</body></html>"""


def build_bug_export_html(export_data):
    """Build a self-contained HTML report from server-validated selected findings."""
    tasks = export_data["tasks"]
    bugs = export_data["bugs"]
    task_cards = "".join(
        "<article class='task-card " + _e(str(item.get("severity", "low")).lower()) + "'>"
        "<div class='task-top'><span class='severity'>" + _e(str(item.get("severity", "N/D")).upper()) + "</span>"
        "<span class='task-id'>" + _e(item.get("id")) + "</span></div>"
        "<p class='repository'>" + _e(item.get("repository")) + "</p>"
        "<h3>" + _e(item.get("title")) + "</h3>"
        "<dl><dt>Archivo</dt><dd><code>" + _e(item.get("file")) + "</code></dd>"
        "<dt>Línea</dt><dd>" + _e(item.get("line")) + "</dd></dl>"
        "<h4>Acción recomendada</h4><p>" + _e(item.get("recommended_action")) + "</p></article>"
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
""" + inline_stylesheet() + """</head><body><header><p>INFORME DE EXPORTACIÓN</p><h1>Informe consolidado de tareas y posibles bugs</h1>
<p>Conjunto: """ + _e(export_data["group_name"]) + """ · Microservicio: """ + _e(export_data["repository"]) + """</p>
<p>Generado: """ + _e(export_data["generated_at"]) + """ · Elementos seleccionados: """ + str(len(tasks)) + """</p></header><main>
<section><h2>Tareas pendientes (""" + str(len(tasks)) + """)</h2>""" + (task_cards or "<p>No hay tareas seleccionadas.</p>") + """</section>
<section><h2>Posibles bugs (""" + str(len(bugs)) + """)</h2>
<div class="table-wrap"><table class="bug-table"><thead><tr><th>Microservicio</th><th>Código</th><th>Título</th><th>Detalle</th><th>Evidencia</th></tr></thead><tbody>""" + bug_rows + """</tbody></table></div></section>
<p>Los elementos son candidatos heurísticos y deben validarse mediante revisión y pruebas.</p>
</main></body></html>"""

def build_bug_reports_index(group_name, reports, repositories=None, group_id=None):
    rows = "".join(
        "<li><a href='" + _e(x["file"]) + "'>" + _e(x["repository"]) +
        "</a> <span class='muted'>· " + _e(x["count"]) + " posibles bugs</span></li>"
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
        for index, finding in enumerate(_repository_bug_findings(repository)):
            label = (
                "<label class='finding-choice'><input class='bug-select' type='checkbox' data-report='" +
                _e(report_name) + "' value='" + str(index) + "' data-repository='" + _e(repository.get("name", "Microservicio")) +
                "' data-service-slug='" + _e(slug) + "' data-finding='" + _e(__import__('json').dumps({**finding, "recommended_action": TASKS.get(finding.get("code"), finding.get("fix_suggestion") or "Revisar el hallazgo y añadir una prueba de regresión.")}, ensure_ascii=False)) + "'><span><b>" +
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
<button id="export-selected-bugs" type="button" data-group-id="__GROUP_ID__" data-group-name="__GROUP_NAME__">Exportar selección (JSON + HTML)</button>
<button id="export-all-bugs-json" type="button" data-group-id="__GROUP_ID__" data-group-name="__GROUP_NAME__">Exportar todos como JSON individuales (revisao.zip)</button>
<span id="export-status" role="status" aria-live="polite">No hay hallazgos seleccionados.</span></div>
<div class="finding-list">""" + "".join(selectable) + """</div></section>"""
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Informes individuales de posibles bugs</title>
""" + stylesheet_link() + """</head><body><header><p>POSIBLES BUGS</p><h1>Informes individuales de posibles bugs</h1><p>Conjunto analizado: """ + _e(group_name) + """</p></header><main><nav class="actions"><a href="../analysis.html">← Informe global</a><a href="../index.html">Índice de documentación</a></nav><section>
<p>Solo aparecen microservicios con uno o más candidatos detectados. Puedes abrir un informe individual o seleccionar hallazgos de varios servicios para exportarlos juntos.</p><ul>""" + rows + """</ul></section>""" + selection_ui.replace("__GROUP_ID__", _e(group_id or "")).replace("__GROUP_NAME__", _e(group_name)) + """</main>""" + (_bug_export_script() if selectable else "") + """</body></html>"""
