"""Índice raíz de la carpeta de informes: enlaza todos los análisis descargados y sus documentos.

Uso:  python -m app.reports_index <carpeta_de_informes>
Genera <carpeta>/index.html con enlaces relativos, por lo que funciona sin conexión.
"""
from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
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


class _FindingParser(HTMLParser):
    """Extrae los hallazgos embebidos en los índices offline de cada análisis."""
    def __init__(self):
        super().__init__()
        self.findings = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "input":
            return
        data = dict(attrs)
        classes = data.get("class", "").split()
        if "bug" not in classes:
            return
        try:
            finding = json.loads(html.unescape(data.get("data-finding", "{}")))
        except (TypeError, ValueError):
            finding = {}
        # El índice de documentación usa atributos separados en cada checkbox.
        for key in ("code", "severity", "file", "line", "title", "description", "excerpt", "confidence"):
            if key not in finding and data.get("data-" + key) is not None:
                finding[key] = data.get("data-" + key)
        self.findings.append({
            "repository": data.get("data-repository", "Microservicio"),
            "finding": finding,
        })


def _findings(bundle: Path) -> list[dict]:
    parser = _FindingParser()
    try:
        parser.feed((bundle / "index.html").read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []
    return parser.findings


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
                        "services": services, "bug_files": bug_files, "findings": _findings(bundle)})
    return sorted(bundles, key=lambda b: (-b["modified"], b["folder"]))


def render(bundles: list[dict]) -> str:
    cards = []
    all_findings = []
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
        for item in b.get("findings", []):
            finding = item["finding"]
            all_findings.append({"bundle": b["title"], "folder": b["folder"],
                                 "repository": item["repository"], **finding})
        cards.append("<section" + (" class='latest'" if position == 0 else "") + "><p class='tag'>" + ("ÚLTIMO ANÁLISIS · " if position == 0 else "") + _e(when) +
                     "</p><h2><a href='" + _href(b["folder"], "index.html") + "'>" + _e(b["title"]) + "</a></h2><p class='muted'>" + _e(b["folder"]) +
                     "</p><div class='links main'>" + links + "</div>" + detail + "</section>")
    body = "".join(cards) or "<section><p>Todavía no hay ningún análisis descargado en esta carpeta.</p></section>"
    finding_rows = []
    for index, item in enumerate(all_findings):
        severity = str(item.get("severity", "low")).lower()
        finding_rows.append(
            "<article class='finding " + _e(severity) + "'><label class='select-finding'><input type='checkbox' class='root-bug' "
            "data-index='" + str(index) + "'> Seleccionar tarea / bug</label>"
            "<div class='top'><b>" + _e(severity.upper()) + "</b><span>" + _e(item.get("code", "N/D")) + "</span></div>"
            "<h3>" + _e(item.get("title", "Posible bug")) + "</h3><p>" + _e(item.get("description", "")) + "</p>"
            "<p class='muted'><b>Análisis:</b> " + _e(item.get("bundle")) + " · <b>Microservicio:</b> " + _e(item.get("repository")) + "</p>"
            "<dl><dt>Archivo</dt><dd><code>" + _e(item.get("file", "N/D")) + "</code></dd><dt>Línea</dt><dd>" + _e(item.get("line", "N/D")) +
            "</dd><dt>Confianza</dt><dd>" + _e(item.get("confidence", "heuristic_candidate")) + "</dd></dl>"
            "<h4>Evidencia</h4><pre>" + _e(item.get("excerpt", "")) + "</pre></article>"
        )
    selection = """<section id="all-work"><h2>Todas las tareas y posibles bugs</h2>
<p>Selecciona hallazgos de cualquiera de los análisis descargados. Puedes combinarlos en una sola exportación.</p>
<div class="toolbar"><label><input id="select-everything" type="checkbox"> Seleccionar todos</label>
<strong id="selected-count">0 seleccionados</strong><button id="export-root" type="button">Exportar selección (JSON + HTML)</button>
<span id="export-status" role="status">Marca los elementos que quieras convertir en tareas.</span></div>""" + (
        "".join(finding_rows) if finding_rows else "<p>No hay hallazgos disponibles en los índices descargados. Regenera los análisis para incorporar los datos.</p>"
    ) + """</section>"""
    payload = json.dumps(all_findings, ensure_ascii=False).replace("</", "<\\/")
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Documentación de análisis</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fb;color:#17243a;font:15px/1.55 system-ui}header{background:linear-gradient(120deg,#102344,#1e477f,#087e83);color:white;padding:34px max(20px,calc((100% - 1100px)/2))}h1{margin:0 0 6px}main{max-width:1100px;margin:24px auto;padding:0 18px}section{background:white;border:1px solid #dce4ef;border-radius:12px;padding:18px 20px;margin:14px 0}section.latest{border-color:#1e7f83;border-width:2px}h2{margin:2px 0;font-size:1.2rem;overflow-wrap:anywhere}a{color:#2457a6;font-weight:700;text-decoration:none}a:hover{text-decoration:underline}.tag{margin:0;font-size:.8rem;letter-spacing:.04em;color:#1e7f83;font-weight:700}.muted{color:#66758a;margin:2px 0 10px;overflow-wrap:anywhere}.links{display:flex;gap:8px 14px;flex-wrap:wrap}.links.main a{padding:8px 12px;border:1px solid #dce4ef;border-radius:8px}details{margin-top:12px}summary{cursor:pointer;font-weight:700}table{border-collapse:collapse;width:100%;margin-top:8px}td{padding:8px 6px;border-bottom:1px solid #e6ebf2;vertical-align:top;overflow-wrap:anywhere}
#all-work{margin-top:24px}.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;position:sticky;top:0;background:white;padding:12px 0;border-bottom:1px solid #e6ebf2;z-index:2}.toolbar button{background:#2457a6;color:white;border:0;border-radius:8px;padding:10px 16px;font:inherit;font-weight:700;cursor:pointer}.finding{background:white;border:1px solid #dce3ed;border-left:5px solid #3975bb;border-radius:12px;padding:16px;margin:13px 0}.finding.high{border-left-color:#c43d4b}.finding.medium{border-left-color:#c28a23}.top{display:flex;gap:12px}.top b{font-size:.8rem;padding:3px 8px;border-radius:20px;background:#edf1f6}.finding.high .top b{background:#fdebed;color:#a62231}.finding.medium .top b{background:#fff3d9;color:#805500}.select-finding{display:inline-flex;gap:8px;color:#2457a6;font-weight:650;margin-bottom:10px}.finding h3{margin:8px 0}.finding h4{margin:12px 0 4px}dl{display:grid;grid-template-columns:90px 1fr;gap:4px 12px}dt{font-weight:650;color:#5b6678}dd{margin:0;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#111c2e;color:#e8efff;padding:13px;border-radius:8px}
@media(max-width:520px){header{padding:25px 18px}dl{grid-template-columns:1fr}}
</style></head><body><header><p>DOCUMENTACIÓN TÉCNICA</p><h1>Todos los análisis</h1><p>""" + str(len(bundles)) + """ análisis descargados · """ + str(len(all_findings)) + """ tareas / posibles bugs · el más reciente aparece primero</p></header><main>""" + selection + body + """
<script>
(function(){
 const data = """ + payload + """;
 const boxes = Array.from(document.querySelectorAll('.root-bug'));
 const all = document.getElementById('select-everything');
 const count = document.getElementById('selected-count');
 const status = document.getElementById('export-status');
 function refresh(){const n=boxes.filter(x=>x.checked).length;count.textContent=n+' seleccionados';all.checked=n===boxes.length&&n>0;all.indeterminate=n>0&&n<boxes.length;}
 boxes.forEach(x=>x.addEventListener('change',refresh));
 all.addEventListener('change',()=>{boxes.forEach(x=>x.checked=all.checked);refresh();});
 document.getElementById('export-root').addEventListener('click',()=>{
  const selected=boxes.filter(x=>x.checked).map(x=>data[Number(x.dataset.index)]);
  if(!selected.length){status.textContent='Selecciona al menos un elemento.';return;}
  const tasks=selected.map((x,i)=>({id:String(x.folder).replace(/[^a-z0-9]+/gi,'-')+'-'+String(x.repository).replace(/[^a-z0-9]+/gi,'-')+'-'+(i+1),
   repository:x.repository,title:x.title||'Posible bug',description:x.description||'',status:'Pendiente',severity:x.severity||'low',
   file:x.file||'N/D',line:x.line||'N/D',confidence:x.confidence||'heuristic_candidate',excerpt:x.excerpt||'',
   recommended_action:x.recommended_action||'Revisar el hallazgo y añadir una prueba de regresión.'}));
  const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const cards=tasks.map(x=>'<article class="task '+esc(x.severity)+'"><b>'+esc(String(x.severity).toUpperCase())+' · '+esc(x.id)+'</b><p>'+esc(x.repository)+'</p><h3>'+esc(x.title)+'</h3><p>'+esc(x.description)+'</p><p><b>Archivo:</b> '+esc(x.file)+':'+esc(x.line)+'</p><h4>Acción recomendada</h4><p>'+esc(x.recommended_action)+'</p><h4>Evidencia</h4><pre>'+esc(x.excerpt)+'</pre></article>').join('');
  const report='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tareas y bugs exportados</title><style>body{font:15px/1.5 system-ui;margin:0;background:#f4f6fa;color:#172033}main{max-width:1000px;margin:25px auto;padding:0 18px}.task{background:white;border:1px solid #dce3ed;border-left:5px solid #3975bb;border-radius:12px;padding:16px;margin:14px 0}.task.high{border-left-color:#c43d4b}.task.medium{border-left-color:#c28a23}pre{white-space:pre-wrap;background:#111c2e;color:white;padding:12px;border-radius:8px}</style><main><h1>Tareas y posibles bugs exportados</h1><p>'+tasks.length+' elementos seleccionados</p>'+cards+'</main></html>';
  const save=(content,type,name)=>{const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();return url;};
  const url=save(report,'text/html;charset=utf-8','tareas-y-bugs.html');window.open(url,'_blank');
  save(JSON.stringify({schema_version:'1.0',generated_at:new Date().toISOString(),total_tasks:tasks.length,tasks,bugs:tasks},null,2),'application/json;charset=utf-8','tareas-y-bugs.json');
  status.textContent=tasks.length+' elementos exportados en JSON y HTML.';
 });
 refresh();
})();
</script></main></body></html>"""




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
