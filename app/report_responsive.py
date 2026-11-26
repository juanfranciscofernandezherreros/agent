"""Shared responsive post-processing for generated HTML reports."""
from pathlib import Path

STYLE = """<style id="agent-responsive-layout">
*,*::before,*::after{box-sizing:border-box}
html,body{max-width:100%;overflow-x:hidden}
body{width:100%;line-height:1.6}
main{width:min(100% - 32px,1440px);max-width:1440px;margin-inline:auto}
header{padding-inline:clamp(16px,4vw,48px);overflow-wrap:anywhere}
img,svg,video,canvas,iframe{max-width:100%;height:auto}
p,li,dd,td,th,a,code{overflow-wrap:anywhere}
pre{max-width:100%;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}
table{width:100%;max-width:100%;border-collapse:separate}
.report-table-scroll{width:100%;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}
.report-table-scroll>table{min-width:620px}
nav,.actions,.doc-links,.selection-actions,.toolbar,.links{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
nav a,.actions a,.doc-links a,button{max-width:100%;white-space:normal;overflow-wrap:anywhere}
section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group{min-width:0;max-width:100%}
input,select,textarea,button{max-width:100%;font:inherit}
@media(max-width:760px){main{width:calc(100% - 24px);margin-block:16px}header{padding:22px 16px!important;border-radius:0 0 16px 16px}section,article{padding:15px!important;margin-block:12px!important}h1{font-size:clamp(1.55rem,7vw,2.2rem)}.report-table-scroll{margin-inline:-4px;width:calc(100% + 8px)}.report-table-scroll>table{min-width:620px}dl{grid-template-columns:1fr!important}dd{margin:0 0 8px}}
@media(max-width:420px){main{width:calc(100% - 18px)}section,article{padding:12px!important}}
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
