"""Responsive post-processing for generated HTML reports.

Keep the technical-sheet layout rules here so both individual and group reports
receive the same predictable responsive behavior.
"""
from pathlib import Path

STYLE = """<style id="agent-responsive-layout-v3">
*,*::before,*::after{box-sizing:border-box;min-width:0}
html,body{width:100%;max-width:100%;overflow-x:clip}
body{line-height:1.6}
main{width:100%;max-width:1440px;margin-inline:auto}
.shell{display:grid;grid-template-columns:minmax(190px,240px) minmax(0,1fr);gap:20px;width:100%;max-width:1440px;margin:24px auto;padding:0 20px;align-items:start}
.shell>main{width:100%!important;min-width:0!important;max-width:none!important;margin:0!important;padding:0!important}
.sidebar{position:sticky;top:16px;display:flex;flex-direction:column;gap:7px;min-width:0;max-width:100%;max-height:calc(100vh - 32px);overflow:auto;padding:14px;background:linear-gradient(180deg,#101722,#0e1520);border:1px solid #26364b;border-radius:14px}
.sidebar>a{display:block;max-width:100%;padding:7px 9px;border:1px solid transparent;border-radius:8px;overflow-wrap:anywhere;text-decoration:none}
.sidebar>a:hover{background:#152235;border-color:#2b405b}
header{max-width:100%;overflow-wrap:anywhere}
img,svg,video,canvas,iframe{max-width:100%;height:auto}
p,li,dd,td,th,a,code,strong,b,small{overflow-wrap:anywhere;word-break:normal}
pre{max-width:100%;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}
.table-wrap,.report-table-scroll{display:block;width:100%;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}
.table-wrap>table,.report-table-scroll>table{width:100%;min-width:620px;max-width:none}
table{border-collapse:separate}
section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group,.kpi,.buggroup,.report-section{min-width:0;max-width:100%}
.metrics,.score-grid,.two-col,.subgrid,.class-grid,.service-map,.risk-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:14px;min-width:0;max-width:100%}
.metrics>*,.score-grid>*,.two-col>*,.subgrid>*,.class-grid>*,.service-map>*,.risk-list>*{min-width:0;max-width:100%}
.quality-banner{display:flex;flex-wrap:wrap;gap:16px;align-items:center}
.quality-banner>*{min-width:0;max-width:100%;flex:1 1 220px}
.catalog-tools{display:flex;flex-wrap:wrap;gap:10px;align-items:center;max-width:100%}
.catalog-tools input{flex:1 1 240px;min-width:0}
.class-card ol,.class-card li{min-width:0;max-width:100%}
input,select,textarea,button{max-width:100%;font:inherit}
@media(max-width:900px){
 .shell{grid-template-columns:minmax(0,1fr);gap:12px;margin:14px auto;padding:0 16px}
 .sidebar{position:static;max-height:none;display:flex;flex-direction:row;flex-wrap:wrap;align-items:center}
 .sidebar>strong{flex:0 0 100%}
 .sidebar>a{flex:0 1 auto}
 .shell>main{padding:0!important}
}
@media(max-width:760px){
 main{width:100%;margin-block:16px!important;padding-inline:12px!important}
 header{padding:22px 16px!important;border-radius:0 0 16px 16px!important}
 .shell{padding:0 12px}
 section,article{padding:15px!important;margin-block:12px!important}
 h1{font-size:clamp(1.55rem,7vw,2.2rem);overflow-wrap:anywhere}
 .metrics,.score-grid,.two-col,.subgrid,.class-grid,.service-map,.risk-list{grid-template-columns:minmax(0,1fr)}
 .hero-meta{display:flex;flex-wrap:wrap;gap:8px}
 .sidebar{gap:6px;padding:10px}
 .sidebar>a{font-size:.88rem;padding:6px 8px}
}
@media(max-width:420px){
 main{padding-inline:9px!important}
 .shell{padding:0 9px}
 section,article{padding:12px!important}
 .table-wrap>table,.report-table-scroll>table{min-width:560px}
}

/* Light palette for the responsive shell and mobile navigation */
:root{color-scheme:light!important;--bg:#f3f6fb;--surface:#fff;--surface2:#f8fafc;--surface3:#eef3f8;--line:#d9e1ec;--text:#253247;--muted:#64748b;--accent:#087f73;--blue:#245bb5}
html,body{background:#f3f6fb!important;color:#253247!important}
.sidebar{background:#fff!important;border-color:#d9e1ec!important;box-shadow:0 5px 18px rgba(31,51,73,.06)!important;color:#253247!important}
.sidebar>strong{color:#1e293b!important}
.sidebar>a{color:#245bb5!important}
.sidebar>a:hover{background:#f1f5f9!important;border-color:#d5dfeb!important}
.table-wrap,.report-table-scroll{background:#fff!important}

/* AGENT project-wide LIGHT theme v3: enforce a single readable light palette. */
:root{color-scheme:light!important;--bg:#f4f7fb!important;--surface:#ffffff!important;--surface2:#f8fafc!important;--surface3:#eef3f8!important;--panel:#ffffff!important;--panel2:#f8fafc!important;--line:#d8e1ec!important;--border:#d8e1ec!important;--text:#243247!important;--muted:#64748b!important;--accent:#087f73!important;--blue:#245bb5!important;--danger:#b42335!important;--warning:#946200!important;--success:#137547!important;--red:#b42335!important;--amber:#946200!important;--green:#137547!important}
html,body{background:#f4f7fb!important;color:#243247!important;color-scheme:light!important}
body{background:#f4f7fb!important;color:#243247!important}
header,.hero{background:linear-gradient(120deg,#e8eff8,#f5f8fc 65%,#e6f3f1)!important;color:#1e293b!important;border-color:#d8e1ec!important;box-shadow:0 8px 24px rgba(31,51,73,.06)!important}
header h1,header h2,header h3,.hero h1,.hero h2{color:#17243a!important}
header p,.hero p{color:#52647a!important}
main{color:#243247!important}
section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group,.kpi,.buggroup,.report-section,.raw-summary,details.data-section,.finding details,.service,.metric,.score-card{background:#fff!important;background-image:none!important;color:#243247!important;border-color:#d8e1ec!important;box-shadow:0 5px 18px rgba(31,51,73,.055)!important}
h1,h2,h3,h4,h5,h6,strong,b,summary,label,dt{color:#1e293b!important}
p,li,dd,td,th,span,div{ text-shadow:none!important}
p,li,dd,td{color:#334155!important}
small,.muted,.note,footer,dt,.section-intro,.finding-number,.empty{color:#64748b!important}
a{color:#245bb5!important}a:hover{color:#087f73!important}
nav,.report-nav,.bugbar{background:rgba(255,255,255,.96)!important;border-color:#d8e1ec!important;box-shadow:0 4px 14px rgba(31,51,73,.06)!important}
nav a,.report-nav a,.actions a,.selection-actions a{background:#f8fafc!important;color:#245bb5!important;border-color:#d8e1ec!important}
nav a:hover,.report-nav a:hover,.actions a:hover{background:#eaf1f8!important;color:#087f73!important;border-color:#b9c9dc!important}
button,.export-panel button,#bug-send{background:#245bb5!important;color:#fff!important;border:1px solid #245bb5!important}
button:hover,.export-panel button:hover,#bug-send:hover{background:#19488f!important;color:#fff!important}
button:disabled{opacity:.6}
input,select,textarea{background:#fff!important;color:#243247!important;border:1px solid #cbd5e1!important;box-shadow:none!important}
input::placeholder,textarea::placeholder{color:#94a3b8!important}
pre,code,kbd,samp{background:#f1f5f9!important;color:#243247!important;border:1px solid #d8e1ec!important}
table{background:#fff!important;color:#243247!important}
table th,thead th{background:#eaf0f6!important;color:#334155!important;border-color:#d8e1ec!important}
td,th{border-color:#e2e8f0!important;color:#334155!important}
tbody tr:hover,tbody tr:hover td{background:#f5f8fc!important}
hr{border-color:#d8e1ec!important}
.metric strong,.kpi strong,.score-card strong,.metric .value{color:#087f73!important}
.count,.tag,.eyebrow,.section-kicker{color:#087f73!important}
.severity.high,.sev-high{background:#fff1f2!important;color:#b42335!important;border-color:#fecdd3!important}
.severity.medium,.sev-medium{background:#fff7e6!important;color:#946200!important;border-color:#f5dfaa!important}
.severity.low{background:#eff6ff!important;color:#245bb5!important;border-color:#bfdbfe!important}
.bad,.badge-danger,.high{color:#b42335!important}.warn,.warning,.medium{color:#946200!important}.ok,.success{color:#137547!important}
.sidebar{background:#fff!important;border-color:#d8e1ec!important;color:#243247!important}
.sidebar>a{color:#245bb5!important}
.sidebar>a:hover{background:#f1f5f9!important}
.report-nav{backdrop-filter:blur(12px)}
.empty{background:#f8fafc!important;border-color:#cbd5e1!important}
@media(prefers-color-scheme:dark){:root{color-scheme:light!important}html,body{background:#f4f7fb!important;color:#243247!important}}
</style><script>(function(){function wrap(){document.querySelectorAll('table').forEach(function(t){if(t.parentElement&&(t.parentElement.classList.contains('report-table-scroll')||t.parentElement.classList.contains('table-wrap')))return;var w=document.createElement('div');w.className='report-table-scroll';t.parentNode.insertBefore(w,t);w.appendChild(t)})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wrap);else wrap()})();</script>"""

def make_folder_responsive(folder):
    root = Path(folder)
    changed = 0
    if not root.exists():
        return changed
    for path in root.rglob("*.html"):
        try:
            original = path.read_text(encoding="utf-8")
            if 'id="agent-responsive-layout-v2"' in original:
                continue
            pos = original.lower().find("</head>")
            if pos < 0:
                pos = original.lower().find("</body>")
            updated = original[:pos] + STYLE + original[pos:] if pos >= 0 else original + STYLE
            path.write_text(updated, encoding="utf-8")
            changed += 1
        except (OSError, UnicodeError):
            continue
    return changed
