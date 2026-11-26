"""Responsive post-processing for generated HTML reports.

Keep the technical-sheet layout rules here so both individual and group reports
receive the same predictable responsive behavior.
"""
from pathlib import Path

STYLE = """<style id="agent-responsive-layout-v2">
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
