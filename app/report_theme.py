"""Single source of truth for the look of every generated HTML report.

All report styling lives in ``app/static/report.css``. Generators never embed
their own ``<style>`` blocks or ``style=""`` attributes; instead they:

* call :func:`stylesheet_link` in ``<head>`` for reports written to a
  workspace folder or served by the API, and
* call :func:`inline_stylesheet` only for self-contained files the user
  downloads (exports), where a relative link could not be resolved. The
  embedded text is read from the same ``report.css`` file.

After a workspace folder has been written, :func:`apply_report_theme` copies
``report.css`` to the folder root and fixes each page's link so it resolves
both from disk (``file://``) and through the API routes.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

CSS_FILENAME = "report.css"
CSS_PATH = Path(__file__).resolve().parent / "static" / CSS_FILENAME
LINK_MARKER = "data-agent-report-css"
INLINE_ID = "agent-report-css"

_LINK_RE = re.compile(r'<link\b[^>]*\b' + LINK_MARKER + r'\b[^>]*>', re.I)
# Legacy theme blocks injected by previous versions (report_responsive v3 and
# per-generator inline themes). Removed when re-theming existing workspaces.
_LEGACY_STYLE_RE = re.compile(r'<style\b(?![^>]*\bid="' + INLINE_ID + r'")[^>]*>.*?</style>', re.I | re.S)
_LEGACY_SCRIPT_RE = re.compile(
    r"<script>\(function\(\)\{function wrap\(\)\{document\.querySelectorAll\('table'\).*?</script>", re.S)


@lru_cache(maxsize=1)
def read_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def stylesheet_link(href: str = CSS_FILENAME) -> str:
    """``<link>`` to the shared stylesheet. ``href`` is fixed up later by
    :func:`apply_report_theme` according to the page's folder depth."""
    return '<link rel="stylesheet" href="' + href + '" ' + LINK_MARKER + '>'


def inline_stylesheet() -> str:
    """Embed ``report.css`` for standalone downloads (same file, same rules)."""
    return '<style id="' + INLINE_ID + '">' + read_css() + "</style>"


def install_stylesheet(folder) -> Path:
    """Copy ``report.css`` into ``folder`` and return the destination."""
    root = Path(folder)
    root.mkdir(parents=True, exist_ok=True)
    target = root / CSS_FILENAME
    css = read_css()
    if not target.is_file() or target.read_text(encoding="utf-8") != css:
        target.write_text(css, encoding="utf-8")
    return target


def relative_href(page: Path, root: Path) -> str:
    rel = os.path.relpath(root / CSS_FILENAME, page.parent)
    return rel.replace(os.sep, "/")


def theme_html(html: str, href: str = CSS_FILENAME) -> str:
    """Return ``html`` linked to the shared stylesheet and without legacy
    inline themes. Self-contained exports (``inline_stylesheet``) are kept."""
    if 'id="' + INLINE_ID + '"' in html:
        return html
    html = _LEGACY_STYLE_RE.sub("", html)
    html = _LEGACY_SCRIPT_RE.sub("", html)
    link = stylesheet_link(href)
    if _LINK_RE.search(html):
        return _LINK_RE.sub(lambda _m: link, html, count=1)
    lower = html.lower()
    pos = lower.find("</head>")
    if pos < 0:
        pos = lower.find("<body")
    if pos < 0:
        return link + html
    return html[:pos] + link + html[pos:]


def apply_report_theme(folder) -> int:
    """Install ``report.css`` in ``folder`` and link every ``*.html`` below it.

    Returns the number of HTML files that changed."""
    root = Path(folder)
    if not root.exists():
        return 0
    install_stylesheet(root)
    changed = 0
    for path in root.rglob("*.html"):
        try:
            original = path.read_text(encoding="utf-8")
            updated = theme_html(original, relative_href(path, root))
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed += 1
        except (OSError, UnicodeError):
            continue
    return changed
