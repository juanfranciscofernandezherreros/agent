"""Shared responsive post-processing for generated HTML reports."""
from pathlib import Path

STYLE = """<style id="agent-responsive-layout">
*,*::before,*::after{box-sizing:border-box;min-width:0}
html,body{width:100%;max-width:100%;overflow-x:hidden}
body{line-height:1.6}
main{width:calc(100% - 32px)!important;max-width:1440px!important;margin-inline:auto!important}
header{max-width:100%;overflow-wrap:anywhere}
img,svg,video,canvas,iframe{max-width:100%;height:auto}
p,li,dd,td,th,a,code,strong,b,small{overflow-wrap:anywhere;word-break:normal}
pre{max-width:100%;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}
table{width:100%;max-width:100%;border-collapse:separate}
.report-table-scroll{display:block;width:100%;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}
.report-table-scroll>table{min-width:620px}
nav,.actions,.doc-links,.selection-actions,.toolbar,.links{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
nav a,.actions a,.doc-links a,button{max-width:100%;white-space:normal;overflow-wrap:anywhere}
section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group,.kpi,.buggroup,.report-section{min-width:0;max-width:100%}
input,select,textarea,button{width:auto;max-width:100%;font:inherit}
.shell{display:grid;grid-template-columns:minmax(210px,260px) minmax(0,1fr);gap:20px;width:100%;max-width:100%;align-items:start}
.shell>main{width:100%!important;min-width:0!important;max-width:none!important;margin:0!important}
.sidebar{min-width:0;max-width:100%;overflow-wrap:anywhere}
.metrics,.score-grid,.two-col,.subgrid,.class-grid,.service-map,.risk-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:14px;min-width:0;max-width:100%}
.metrics>* ,.score-grid>*,.two-col>*,.subgrid>*,.class-grid>*,.service-map>*,.risk-list>*{min-width:0;max-width:100%}
.quality-banner{display:flex;flex-wrap:wrap;gap:16px;align-items:center}
.quality-banner>*{min-width:0;max-width:100%;flex:1 1 220px}
.catalog-tools{display:flex;flex-wrap:wrap;gap:10px;align-items:center;max-width:100%}
.catalog-tools input{flex:1 1 240px;min-width:0}
.class-card ol,.class-card li{min-width:0;max-width:100%}
@media(max-width:900px){.shell{grid-template-columns:minmax(0,1fr)}.sidebar{position:static;width:100%}.sidebar nav,.sidebar a{max-width:100%}}
@media(max-width:760px){
 main{width:calc(100% - 24px)!important;margin-block:16px!important}
 header{padding:22px 16px!important;border-radius:0 0 16px 16px!important}
 section,article{padding:15px!important;margin-block:12px!important}
 h1{font-size:clamp(1.55rem,7vw,2.2rem);overflow-wrap:anywhere}
 .report-table-scroll{margin-inline:-4px;width:calc(100% + 8px)}
 .report-table-scroll>table{min-width:620px}
 dl{grid-template-columns:minmax(0,1fr)!important}
 dd{margin:0 0 8px}
 .metrics,.score-grid,.two-col,.subgrid,.class-grid,.service-map,.risk-list{grid-template-columns:minmax(0,1fr)}
 .hero-meta{display:flex;flex-wrap:wrap;gap:8px}
}
@media(max-width:420px){main{width:calc(100% - 18px)!important}section,article{padding:12px!important}.report-table-scroll>table{min-width:560px}}
</style><script>(function(){function wrap(){document.querySelectorAll('table').forEach(function(t){if(t.parentElement&&t.parentElement.classList.contains('report-table-scroll'))return;var w=document.createElement('div');w.className='report-table-scroll';t.parentNode.insertBefore(w,t);w.appendChild(t)})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wrap);else wrap()})();</script>"""

def make_folder_responsive(folder):
    root = Path(folder)
    changed = 0
    if not root.exists():
        return changed
    for path in root.rglob("*.html"):
        try:
            original = path.read_text(encoding="utf-8")
            if 'id="agent-responsive-layout"' in original:
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
