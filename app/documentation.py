"""Cross-linked offline documentation index for a complete group analysis."""
from __future__ import annotations
import html
import json
from .report_theme import inline_stylesheet, stylesheet_link

def _e(value):
    return html.escape(str(value if value is not None else ""), quote=True)

def _validation_label(repo):
    status = (repo.get("agent_insights", {}).get("cross_validation") or {}).get("status")
    return {"CONSISTENT": "Coherente", "WARNINGS": "Con avisos", "CONTRADICTIONS": "Con contradicciones"}.get(status, "Ver informe")

def _activity(repo):
    return (repo.get("agent_insights") or {}).get("activity_analysis")


def _activity_cell(repo):
    a = _activity(repo)
    if not a:
        return "<span>Sin datos</span>"
    artifact = str(repo.get("artifact_dir", "")).replace("\\", "/")
    return "<a href='" + _e(artifact + "/activity.html") + "'>" + str(a["commits"]["total"]) + " commits</a> · " + str(a["branches"]["recent"]) + " ramas<small>" + str(a["pushes"]["total"]) + " pushes</small>"


def _activity_section(repos, analysis):
    """Ranking de los microservicios en los que más se está trabajando (histórico Git reciente)."""
    data = []
    for repo in repos:
        a = _activity(repo)
        artifact = str(repo.get("artifact_dir", "")).replace("\\", "/")
        if a and artifact.startswith("repositories/"):
            data.append((repo, a, artifact))
    if not data:
        return ("<section><h2>Microservicios más trabajados</h2><p>No hay histórico de Git disponible. Se obtiene de la API de GitLab "
                "al analizar un grupo (no con listas manuales de repositorios) y necesita un token con permiso read_api.</p></section>")
    days = data[0][1].get("window_days")
    data.sort(key=lambda x: (-x[1]["commits"]["total"], -x[1]["branches"]["recent"], -x[1]["pushes"]["total"], str(x[0].get("name"))))
    top_commits = max(x[1]["commits"]["total"] for x in data) or 1

    def leader(label, key, unit):
        repo, a, artifact = max(data, key=key)
        value = key((repo, a, artifact))
        if not value:
            return "<div class='kpi'><small>" + _e(label) + "</small><b>Sin actividad</b></div>"
        return ("<div class='kpi'><small>" + _e(label) + "</small><b><a href='" + _e(artifact + "/activity.html") + "'>" + _e(repo.get("name")) +
                "</a></b><span>" + _e(value) + " " + _e(unit) + "</span></div>")

    kpis = (leader("Más commits", lambda x: x[1]["commits"]["total"], "commits") +
            leader("Más ramas recientes", lambda x: x[1]["branches"]["recent"], "ramas con actividad") +
            leader("Más pushes", lambda x: x[1]["pushes"]["total"], "pushes"))
    pusher = ((analysis.get("agent_insights") or {}).get("group_activity") or {}).get("top_pusher")
    if pusher:
        kpis += ("<div class='kpi'><small>Usuario con más pushes</small><b>" + _e(pusher.get("display_name") or pusher.get("user")) +
                 "</b><span>" + _e(pusher.get("count")) + " pushes en " + _e(pusher.get("repositories")) + " repositorios</span></div>")
    rows = []
    for position, (repo, a, artifact) in enumerate(data, 1):
        commits, top = a["commits"]["total"], a["pushes"].get("top_user") or {}
        width = max(2, round(100 * commits / top_commits)) if commits else 0
        rows.append("<tr><td>" + str(position) + "</td><td><b><a href='" + _e(artifact + "/activity.html") + "'>" + _e(repo.get("name")) + "</a></b></td>"
                    "<td><progress class='bar' max='100' value='" + str(width) + "'>" + str(width) + "%</progress> " + str(commits) + ("+" if a["commits"].get("truncated") else "") + "</td>"
                    "<td>" + str(a["branches"]["recent"]) + " de " + str(a["branches"]["total"]) + "</td><td>" + str(a["pushes"]["total"]) + "</td>"
                    "<td>" + (_e(top.get("display_name") or top.get("user")) + " (" + _e(top.get("count")) + ")" if top else "—") + "</td>"
                    "<td>" + _e(str(a["commits"].get("last_commit_at") or "—")[:10]) + "</td></tr>")
    missing = len(repos) - len(data)
    return ("<section><h2>Microservicios más trabajados (últimos " + _e(days) + " días)</h2><div class='kpis'>" + kpis + "</div>"
            "<div class='table-wrap'><table><thead><tr><th>#</th><th>Microservicio</th><th>Commits</th><th>Ramas recientes</th><th>Pushes</th>"
            "<th>Quien más empuja</th><th>Último commit</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
            "<p><small>Ordenado por commits recientes en todas las ramas. Datos de la API de GitLab, obtenidos tras el análisis estático de cada repositorio."
            + (" " + str(missing) + " microservicios sin datos de actividad." if missing else "") +
            " <a href='activity.html'>Ver el histórico completo</a> (rankings por ramas y pushes, usuarios y autores).</small></p></section>")


SEVERITY = {"high": ("Alta", 0), "medium": ("Media", 1), "low": ("Baja", 2)}


def _bug_selection_section(repos, bug_by_repo):
    """Lista seleccionable y exportable de todos los posibles bugs en modo offline."""
    groups, total = [], 0
    for index, repo in enumerate(repos):
        candidates = (repo.get("quality_analysis") or {}).get("bug_candidates") or []
        if not candidates:
            continue
        name = repo.get("name")
        bug = bug_by_repo.get(name)
        ordered = sorted(candidates, key=lambda x: (SEVERITY.get(x.get("severity"), ("", 3))[1], str(x.get("file")), x.get("line") or 0))
        rows = []
        for x in ordered:
            label = SEVERITY.get(x.get("severity"), (str(x.get("severity") or "N/D"), 3))[0]
            ref = str(x.get("code")) + "@" + str(x.get("file")) + ":" + str(x.get("line"))
            rows.append("<tr><td><input type='checkbox' class='bug' data-repository='" + _e(name) + "' data-ref='" + _e(ref) + "' data-code='" + _e(x.get("code")) +
                        "' data-severity='" + _e(x.get("severity")) + "' data-file='" + _e(x.get("file")) + "' data-line='" + _e(x.get("line")) +
                        "' data-title='" + _e(x.get("title")) + "' data-description='" + _e(x.get("description")) + "' data-excerpt='" + _e(x.get("excerpt")) + "' data-confidence='" + _e(x.get("confidence", "heuristic_candidate")) + "' aria-label='Seleccionar " + _e(ref) + "'></td><td><span class='sev sev-" + _e(x.get("severity")) + "'>" + _e(label) +
                        "</span></td><td><b>" + _e(x.get("title")) + "</b><small>" + _e(x.get("code")) + "</small></td><td><code>" + _e(x.get("file")) + ":" + _e(x.get("line")) +
                        "</code><small>" + _e(str(x.get("excerpt") or "")[:160]) + "</small></td></tr>")
        total += len(ordered)
        link = (" · <a href='bug-reports/" + _e(bug.get("file")) + "'>Ver expediente</a>") if bug else ""
        groups.append("<details class='buggroup'" + (" open" if len(groups) == 0 else "") + "><summary><label class='pick' onclick='event.stopPropagation()'><input type='checkbox' class='bug-all' data-group='g" + str(index) +
                      "' aria-label='Seleccionar todos los de " + _e(name) + "'></label> <b>" + _e(name) + "</b> · " + str(len(ordered)) + " posibles bugs" + link +
                      "</summary><div class='table-wrap'><table data-group='g" + str(index) + "'><thead><tr><th></th><th>Prioridad</th><th>Posible bug</th><th>Ubicación</th></tr></thead><tbody>" +
                      "".join(rows) + "</tbody></table></div></details>")
    if not groups:
        return "<section id='bugs'><h2>Selección de posibles bugs</h2><p>No se han detectado candidatos a bug en este análisis.</p></section>"
    return ("<section id='bugs'><h2>Selección de posibles bugs</h2><p>Marca los posibles bugs que quieras encargar. " + str(total) +
            " candidatos en " + str(len(groups)) + " microservicios, ordenados por prioridad.</p>"
            "<div class='bugbar'><label><input type='checkbox' id='bug-everything'> Seleccionar todos</label>"
            "<span id='bug-count'>0 seleccionados</span>"
            "<button type='button' id='bug-send'>Exportar selección (JSON + HTML)</button>"
            "<span id='bug-export-status' role='status' aria-live='polite'>Selecciona los hallazgos que quieras exportar.</span></div>" + "".join(groups) +
            """<script>
var AGENT_REPORT_CSS = """ + json.dumps(inline_stylesheet()) + """;
(function () {
  var boxes = Array.prototype.slice.call(document.querySelectorAll('input.bug'));
  var groupBoxes = Array.prototype.slice.call(document.querySelectorAll('input.bug-all'));
  var everything = document.getElementById('bug-everything');
  var count = document.getElementById('bug-count');
  // Punto de enganche para el agente que implemente el envío: devuelve la selección actual.
  window.selectedBugs = function () {
    return boxes.filter(function (b) { return b.checked; }).map(function (b) {
      return { repository: b.dataset.repository, ref: b.dataset.ref, code: b.dataset.code, severity: b.dataset.severity,
               file: b.dataset.file, line: Number(b.dataset.line) || null, title: b.dataset.title,
               description: b.dataset.description, excerpt: b.dataset.excerpt, confidence: b.dataset.confidence };
    });
  };
  function inGroup(g) { return Array.prototype.slice.call(document.querySelectorAll("table[data-group='" + g + "'] input.bug")); }
  function refresh() {
    var n = boxes.filter(function (b) { return b.checked; }).length;
    count.textContent = n + (n === 1 ? ' seleccionado' : ' seleccionados');
    everything.checked = n === boxes.length; everything.indeterminate = n > 0 && n < boxes.length;
    groupBoxes.forEach(function (g) {
      var items = inGroup(g.dataset.group), m = items.filter(function (b) { return b.checked; }).length;
      g.checked = m === items.length; g.indeterminate = m > 0 && m < items.length;
    });
  }
  boxes.forEach(function (b) { b.addEventListener('change', refresh); });
  groupBoxes.forEach(function (g) { g.addEventListener('change', function () {
    inGroup(g.dataset.group).forEach(function (b) { b.checked = g.checked; }); refresh(); }); });
  everything.addEventListener('change', function () { boxes.forEach(function (b) { b.checked = everything.checked; }); refresh(); });
  var send = document.getElementById('bug-send');
  var status = document.getElementById('bug-export-status');
  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[ch];
    });
  }
  send.addEventListener('click', function () {
    var selected = window.selectedBugs();
    if (!selected.length) { status.textContent = 'Selecciona al menos un posible bug.'; return; }
    var tasks = selected.map(function (item, i) {
      return {id: item.repository.replace(/[^a-z0-9]+/gi, '-') + '-' + (i + 1),
        repository: item.repository, title: item.title, description: item.description,
        status: 'Pendiente', severity: item.severity, file: item.file, line: item.line,
        confidence: item.confidence, excerpt: item.excerpt,
        recommended_action: 'Revisar el hallazgo y añadir una prueba de regresión.'};
    });
    var data = {schema_version:'1.0', group_name: document.title.replace('Índice documental - ', ''),
      generated_at:new Date().toISOString(), total_tasks:tasks.length, total_bugs:tasks.length,
      tasks:tasks, bugs:tasks};
    var taskCards = tasks.map(function (x) {
      var severity = String(x.severity || 'low').toLowerCase();
      return '<article class="task-card '+escapeHtml(severity)+'"><div class="task-top"><span class="severity">'+escapeHtml(severity.toUpperCase())+'</span><span class="task-id">'+escapeHtml(x.id)+'</span></div>'+
        '<p class="repository">'+escapeHtml(x.repository)+'</p><h3>'+escapeHtml(x.title)+'</h3>'+
        '<dl><dt>Archivo</dt><dd><code>'+escapeHtml(x.file)+'</code></dd><dt>Línea</dt><dd>'+escapeHtml(x.line)+'</dd></dl>'+
        '<h4>Acción recomendada</h4><p>'+escapeHtml(x.recommended_action)+'</p></article>';
    }).join('');
    var bugRows = tasks.map(function (x) {
      return '<tr>' + [x.repository,x.title,x.description,x.file + ':' + x.line,x.excerpt].map(function(v){return '<td>'+escapeHtml(v)+'</td>';}).join('') + '</tr>';
    }).join('');
    var html = '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Exportación de tareas y bugs</title>' + AGENT_REPORT_CSS + '</head><body><header><p>INFORME DE EXPORTACIÓN</p><h1>Tareas y posibles bugs seleccionados</h1><p>Conjunto: '+escapeHtml(data.group_name)+'</p></header><main><p>'+tasks.length+' tareas seleccionadas</p><h2>Tareas pendientes</h2>'+(taskCards||'<p>No hay tareas seleccionadas.</p>')+'<section class="panel"><h2>Posibles bugs</h2><div class="table-wrap"><table><tr><th>Microservicio</th><th>Título</th><th>Detalle</th><th>Ubicación</th><th>Evidencia</th></tr>'+bugRows+'</table></div></section></main></body></html>';
    function download(content, type, filename) {
      var url = URL.createObjectURL(new Blob([content], {type:type}));
      var a = document.createElement('a'); a.href=url; a.download=filename;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function(){URL.revokeObjectURL(url);},60000);
      return url;
    }
    send.disabled = true;
    var htmlUrl = download(html, 'text/html;charset=utf-8', 'informe-tareas-y-bugs.html');
    // Abrir una vista del HTML exportado en otra pestaña; window.open se ejecuta
    // directamente dentro del clic para evitar que el navegador bloquee el popup.
    var preview = window.open(htmlUrl, '_blank');
    download(JSON.stringify(data,null,2), 'application/json;charset=utf-8', 'tareas-y-bugs.json');
    send.disabled = false;
    status.textContent = selected.length + ' hallazgos exportados. El HTML se ha descargado' +
      (preview ? ' y abierto en otra pestaña para que puedas revisarlo.' : '. Si el navegador bloqueó la pestaña, abre informe-tareas-y-bugs.html desde Descargas.');
  });
  refresh();
})();
</script></section>""")


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
        rows.append("<tr><td><b>" + _e(repo.get("name")) + "</b><small>Commit: " + _e(repo.get("inventory", {}).get("commit_sha", "N/D")) + "</small></td><td>" + _e(quality.get("score", "N/D")) + "/100 · " + _e(quality.get("rating", "N/D")) + "</td><td>" + _activity_cell(repo) + "</td><td><a href='" + _e(artifact + "/analysis.html") + "'>Ficha técnica</a></td><td><a href='" + _e(artifact + "/agents.html") + "'>" + _e(_validation_label(repo)) + "</a></td><td>" + bug_link + "</td></tr>")
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Índice documental - """ + _e(group_name) + """</title>""" + stylesheet_link() + """</head><body><header><p>DOCUMENTACIÓN TÉCNICA · """ + _e(analysis.get("completion_status", "STATIC_ANALYSIS_COMPLETED")) + """</p><h1>""" + _e(group_name) + """</h1><p>Índice de navegación de la documentación generada para el conjunto de microservicios.</p><p>""" + str(len(repos)) + """ microservicios · """ + str(len(bugs)) + """ informes de posibles bugs</p></header><main>
<section><h2>Visión global</h2><div class="actions"><a href="../index.html">← Todos los análisis</a><a href="analysis.html">Abrir informe global de arquitectura y calidad</a><a href="activity.html">Abrir histórico de actividad (ramas, commits y pushes)</a><a href="agents.html">Abrir informe multiagente (LLM y validación cruzada)</a><a href="bug-reports/index.html">Abrir índice de posibles bugs</a><a href="#bugs">Seleccionar posibles bugs</a></div><p>Empieza por el informe global para entender el contexto y las relaciones. Desde allí puedes abrir cada ficha técnica y cada expediente de posibles bugs.</p></section>
""" + _activity_section(repos, analysis) + """
<section><h2>Documentación por microservicio</h2><div class="table-wrap"><table><thead><tr><th>Microservicio</th><th>Calidad estática</th><th>Actividad reciente</th><th>Ficha técnica</th><th>Informe multiagente</th><th>Posibles bugs</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></div></section>
""" + _bug_selection_section(repos, bug_by_repo) + """
<section><h2>Cómo interpretar los documentos</h2><p>Los informes se basan en análisis estático. Las detecciones de bugs, las puntuaciones y las relaciones entre servicios son indicios que requieren validación. No se han ejecutado los servicios ni sus pruebas.</p></section></main></body></html>"""
