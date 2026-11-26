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
    return r"""<script>
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
        htmlContent = "<!doctype html><html lang='es'><meta charset='utf-8'><title>Exportación de tareas y bugs</title><style>
/* AGENT unified report theme v2 */
:root{color-scheme:dark;--bg:#080b12;--surface:#101722;--surface2:#151f2d;--surface3:#1b293a;--line:#26364b;--text:#e7edf7;--muted:#91a2b9;--accent:#64d8c5;--blue:#83adff;--danger:#ff7385;--warning:#f4c56a;--success:#65d6a5}
*{box-sizing:border-box}
html{scroll-behavior:smooth;background:var(--bg)}
body{background:radial-gradient(ellipse at 12% 0%,rgba(39,87,125,.18),transparent 35%),var(--bg)!important;color:var(--text)!important;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;line-height:1.58}
header{background:linear-gradient(125deg,#101b2b 0%,#142b40 58%,#123a3b 100%)!important;color:var(--text)!important;border:1px solid var(--line);border-radius:0 0 22px 22px;padding:30px clamp(18px,4vw,48px)!important;box-shadow:0 20px 55px rgba(0,0,0,.22)}
header h1,h1{letter-spacing:-.04em;line-height:1.12;font-weight:780}
header p:first-child,.section-kicker{color:var(--accent)!important;font-size:.75rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase}
main{max-width:1280px!important;margin:28px auto!important;padding:0 20px!important}
section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group{background:linear-gradient(180deg,var(--surface),#0e1520)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:16px!important;box-shadow:0 10px 30px rgba(0,0,0,.16)!important}
section,article{padding:clamp(16px,2.5vw,26px)!important;margin:16px 0!important}
h2{color:#f0f5ff!important;letter-spacing:-.025em;font-weight:750}
h3,h4{color:#dce8f8!important}
.metric,.kpi,.score-card{background:linear-gradient(145deg,var(--surface2),var(--surface3))!important;border-color:#30445c!important}
.metric strong,.kpi strong,.score-card strong{color:var(--accent)!important}
nav{gap:9px!important}
nav a,.actions a,button{background:#152235!important;color:#cfe0f6!important;border:1px solid #2b405b!important;border-radius:10px!important;padding:8px 12px!important;text-decoration:none!important;transition:all .15s ease}
nav a:hover,.actions a:hover,button:hover{background:#1d314a!important;border-color:#4d7994!important;color:#fff!important}
a{color:var(--blue)!important}a:hover{color:var(--accent)!important}
.muted,small,.note,footer,dt{color:var(--muted)!important}
.note{background:#132233!important;border-left:3px solid var(--accent)!important;border-radius:10px!important;padding:12px 15px!important}
table{border-collapse:separate!important;border-spacing:0!important;width:100%}
table th{background:#172436!important;color:#aebed3!important;font-size:.76rem!important;letter-spacing:.07em;text-transform:uppercase}
td,th{border-color:var(--line)!important;padding:11px 12px!important}
tbody tr:hover td{background:rgba(102,157,204,.055)!important}
pre,code{background:#080e17!important;color:#d7e6ff!important;border:1px solid #26364b!important;border-radius:9px!important}
input,select,textarea{background:#0b1320!important;color:var(--text)!important;border:1px solid #2b3b50!important;border-radius:9px!important}
.bad,.badge-danger{color:var(--danger)!important}.warn,.warning{color:var(--warning)!important}.ok,.success{color:var(--success)!important}
hr{border-color:var(--line)!important}
@media(max-width:700px){main{padding:0 12px!important;margin:18px auto!important}header{padding:22px 18px!important;border-radius:0 0 16px 16px}section,article{padding:15px!important}table{min-width:620px}nav a,.actions a{font-size:.88rem}}
</style><h1>Tareas y posibles bugs</h1><p>Conjunto: "+esc(groupName)+" · Microservicios: "+esc(exportData.repository)+"</p><h2>Tareas pendientes</h2><table><tr><th>ID</th><th>Microservicio</th><th>Hallazgo</th><th>Ubicación</th><th>Severidad</th><th>Acción recomendada</th></tr>"+taskRows+"</table><h2>Posibles bugs</h2><table><tr><th>Microservicio</th><th>Código</th><th>Título</th><th>Detalle</th><th>Evidencia</th></tr>"+bugRows+"</table></html>";
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
</script>"""

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

    styles = """
.export-panel{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.export-panel button{background:#2457c5;color:white;border:0;border-radius:8px;padding:10px 16px;font-weight:700;cursor:pointer}
.export-panel button:disabled{opacity:.6;cursor:wait}
.select-finding{display:inline-flex;align-items:center;gap:8px;font-weight:650;color:#2457c5;margin-bottom:10px}
"""
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Posibles bugs - """ + _e(repository) + """</title><style>
/* AGENT unified report theme */
:root{color-scheme:dark;--bg:#080d18;--panel:#101827;--panel2:#141f31;--border:#26344a;--text:#e8eef8;--muted:#95a5bd;--accent:#65d6c4;--blue:#7ca8ff}
html,body{background:var(--bg)!important;color:var(--text)!important}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif!important}
header{background:linear-gradient(120deg,#0b1222,#142a45,#123a42)!important;color:var(--text)!important;border-bottom:1px solid var(--border)}
main{max-width:1240px!important}section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group{background:var(--panel)!important;color:var(--text)!important;border-color:var(--border)!important;border-radius:14px!important;box-shadow:0 8px 28px rgba(0,0,0,.16)}
section.latest{border-color:#2c7778!important}.metric,.kpi,.score-card{background:var(--panel2)!important}.muted,small,.note,footer,dt{color:var(--muted)!important}
a{color:var(--blue)!important}a:hover{color:var(--accent)!important}button{border-radius:9px!important}pre,code{background:#070c14!important;color:#d8e6ff!important;border:1px solid #26344a}table th{background:#172337!important;color:#aebed3!important}td,th{border-color:var(--border)!important}input,select,textarea{background:#0b1322!important;color:var(--text)!important;border-color:var(--border)!important}

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
<style>
/* AGENT unified report theme */
:root{color-scheme:dark;--bg:#080d18;--panel:#101827;--panel2:#141f31;--border:#26344a;--text:#e8eef8;--muted:#95a5bd;--accent:#65d6c4;--blue:#7ca8ff}
html,body{background:var(--bg)!important;color:var(--text)!important}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif!important}
header{background:linear-gradient(120deg,#0b1222,#142a45,#123a42)!important;color:var(--text)!important;border-bottom:1px solid var(--border)}
main{max-width:1240px!important}section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group{background:var(--panel)!important;color:var(--text)!important;border-color:var(--border)!important;border-radius:14px!important;box-shadow:0 8px 28px rgba(0,0,0,.16)}
section.latest{border-color:#2c7778!important}.metric,.kpi,.score-card{background:var(--panel2)!important}.muted,small,.note,footer,dt{color:var(--muted)!important}
a{color:var(--blue)!important}a:hover{color:var(--accent)!important}button{border-radius:9px!important}pre,code{background:#070c14!important;color:#d8e6ff!important;border:1px solid #26344a}table th{background:#172337!important;color:#aebed3!important}td,th{border-color:var(--border)!important}input,select,textarea{background:#0b1322!important;color:var(--text)!important;border-color:var(--border)!important}

body{font:15px/1.5 system-ui;margin:0;background:#f4f6fa;color:#172033}
main{max-width:1100px;margin:32px auto;padding:0 18px}
section{background:white;border:1px solid #dce3ed;border-radius:12px;padding:20px;margin:16px 0}
.task-card{background:#fff;border:1px solid #dce3ed;border-left:5px solid #3975bb;border-radius:12px;padding:16px;margin:13px 0}
.task-card.high{border-left-color:#c43d4b}.task-card.medium{border-left-color:#c28a23}.task-card.low{border-left-color:#3975bb}
.task-top{display:flex;gap:10px;align-items:center}.severity{font-size:.78rem;font-weight:750;padding:3px 9px;border-radius:20px;background:#edf1f6}
.high .severity{background:#fdebed;color:#a62231}.medium .severity{background:#fff3d9;color:#805500}
.task-id{color:#66758a;font-size:.85rem;font-weight:650}.repository{color:#5b6678;font-weight:650;margin:9px 0 0}
.task-card h3{font-size:1.12rem;margin:5px 0 10px}.task-card h4{margin:12px 0 3px;color:#40516a}
dl{display:grid;grid-template-columns:75px 1fr;gap:4px 12px;margin:10px 0}dt{font-weight:650;color:#5b6678}dd{margin:0;overflow-wrap:anywhere}
code{overflow-wrap:anywhere}.bug-table{width:100%;border-collapse:collapse}.bug-table th,.bug-table td{text-align:left;vertical-align:top;padding:9px;border-bottom:1px solid #e5eaf1;overflow-wrap:anywhere}
.bug-table th{background:#edf1f6}h1,h2{color:#172b4d}
@media(max-width:520px){dl{grid-template-columns:1fr}dd{margin-bottom:6px}}
</style></head><body><main><h1>Informe consolidado de tareas y posibles bugs</h1>
<p>Conjunto: """ + _e(export_data["group_name"]) + """ · Microservicio: """ + _e(export_data["repository"]) + """</p>
<p>Generado: """ + _e(export_data["generated_at"]) + """ · Elementos seleccionados: """ + str(len(tasks)) + """</p>
<section><h2>Tareas pendientes (""" + str(len(tasks)) + """)</h2>""" + (task_cards or "<p>No hay tareas seleccionadas.</p>") + """</section>
<section><h2>Posibles bugs (""" + str(len(bugs)) + """)</h2>
<table class="bug-table"><thead><tr><th>Microservicio</th><th>Código</th><th>Título</th><th>Detalle</th><th>Evidencia</th></tr></thead><tbody>""" + bug_rows + """</tbody></table></section>
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
<style>
/* AGENT unified report theme */
:root{color-scheme:dark;--bg:#080d18;--panel:#101827;--panel2:#141f31;--border:#26344a;--text:#e8eef8;--muted:#95a5bd;--accent:#65d6c4;--blue:#7ca8ff}
html,body{background:var(--bg)!important;color:var(--text)!important}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif!important}
header{background:linear-gradient(120deg,#0b1222,#142a45,#123a42)!important;color:var(--text)!important;border-bottom:1px solid var(--border)}
main{max-width:1240px!important}section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group{background:var(--panel)!important;color:var(--text)!important;border-color:var(--border)!important;border-radius:14px!important;box-shadow:0 8px 28px rgba(0,0,0,.16)}
section.latest{border-color:#2c7778!important}.metric,.kpi,.score-card{background:var(--panel2)!important}.muted,small,.note,footer,dt{color:var(--muted)!important}
a{color:var(--blue)!important}a:hover{color:var(--accent)!important}button{border-radius:9px!important}pre,code{background:#070c14!important;color:#d8e6ff!important;border:1px solid #26344a}table th{background:#172337!important;color:#aebed3!important}td,th{border-color:var(--border)!important}input,select,textarea{background:#0b1322!important;color:var(--text)!important;border-color:var(--border)!important}

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

/* AGENT premium visual layer */
:root{color-scheme:dark!important;--bg:#080b12;--surface:#101722;--surface2:#151f2d;--surface3:#1b293a;--line:#26364b;--text:#e7edf7;--muted:#91a2b9;--accent:#64d8c5;--blue:#83adff;--danger:#ff7385;--warning:#f4c56a;--success:#65d6a5}
*{box-sizing:border-box}html,body{background:radial-gradient(ellipse at 12% 0%,rgba(39,87,125,.2),transparent 35%),var(--bg)!important;color:var(--text)!important;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;line-height:1.6!important}
body{min-height:100vh}header{background:linear-gradient(125deg,#101b2b 0%,#142b40 58%,#123a3b 100%)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:0 0 22px 22px!important;padding:clamp(22px,4vw,42px)!important;box-shadow:0 20px 55px rgba(0,0,0,.24)!important}header h1,h1{letter-spacing:-.04em!important;line-height:1.12!important;font-weight:800!important}header p:first-child,.section-kicker{color:var(--accent)!important;font-size:.75rem!important;font-weight:800!important;letter-spacing:.13em!important;text-transform:uppercase!important}
main{max-width:1280px!important;margin:28px auto!important;padding:0 20px!important}section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group,.kpi,.buggroup{background:linear-gradient(180deg,var(--surface),#0e1520)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:16px!important;box-shadow:0 10px 30px rgba(0,0,0,.18)!important}section,article{padding:clamp(16px,2.5vw,26px)!important;margin:16px 0!important}
h2{color:#f0f5ff!important;letter-spacing:-.025em!important;font-weight:760!important}h3,h4{color:#dce8f8!important}p,li,td{color:var(--text)!important}.metric,.kpi,.score-card{background:linear-gradient(145deg,var(--surface2),var(--surface3))!important;border-color:#30445c!important}.metric strong,.kpi strong,.score-card strong{color:var(--accent)!important}
nav,.actions,.selection-actions{display:flex;gap:9px!important;flex-wrap:wrap!important;align-items:center!important}nav a,.actions a,button{background:#152235!important;color:#cfe0f6!important;border:1px solid #2b405b!important;border-radius:10px!important;padding:8px 12px!important;text-decoration:none!important;transition:all .15s ease!important}nav a:hover,.actions a:hover,button:hover{background:#1d314a!important;border-color:#4d7994!important;color:#fff!important}a{color:var(--blue)!important}a:hover{color:var(--accent)!important}.muted,small,.note,footer,dt{color:var(--muted)!important}.note{background:#132233!important;border-left:3px solid var(--accent)!important;border-radius:10px!important;padding:12px 15px!important}
table{border-collapse:separate!important;border-spacing:0!important;width:100%!important}table th{background:#172436!important;color:#aebed3!important;font-size:.76rem!important;letter-spacing:.07em!important;text-transform:uppercase!important}td,th{border-color:var(--line)!important;padding:11px 12px!important;vertical-align:top!important}tbody tr:hover td{background:rgba(102,157,204,.06)!important}pre,code{background:#080e17!important;color:#d7e6ff!important;border:1px solid #26364b!important;border-radius:9px!important}pre{white-space:pre-wrap!important;overflow-wrap:anywhere!important}input,select,textarea{background:#0b1320!important;color:var(--text)!important;border:1px solid #2b3b50!important;border-radius:9px!important}.bad,.badge-danger,.high{color:var(--danger)!important}.warn,.warning,.medium{color:var(--warning)!important}.ok,.success{color:var(--success)!important}hr{border-color:var(--line)!important}.empty{color:var(--muted)!important;border:1px dashed var(--line)!important;border-radius:12px!important;padding:14px!important}
@media(max-width:700px){main{padding:0 12px!important;margin:18px auto!important}header{padding:22px 18px!important;border-radius:0 0 16px 16px!important}section,article{padding:15px!important}table{min-width:620px!important}nav a,.actions a{font-size:.88rem!important}}
</style></head><body><main><section><nav class="actions"><a href="../analysis.html">← Informe global</a><a href="../index.html">Índice de documentación</a></nav>
<h1>Informes individuales de posibles bugs</h1><p>Conjunto analizado: """ + _e(group_name) + """</p>
<p>Solo aparecen microservicios con uno o más candidatos detectados. Puedes abrir un informe individual o seleccionar hallazgos de varios servicios para exportarlos juntos.</p><ul>""" + rows + """</ul></section>""" + selection_ui.replace("__GROUP_ID__", _e(group_id or "")).replace("__GROUP_NAME__", _e(group_name)) + """</main>""" + (_bug_export_script() if selectable else "") + """</body></html>"""
