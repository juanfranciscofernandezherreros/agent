from pathlib import Path
import ast
import html
import json
import re
from .report_theme import stylesheet_link

SECRET = re.compile(r"(?i)(password|secret|token|api[_-]?key|private[_-]?key)(\s*[=:]\s*)[^\s,;]+")

def analyze_functional_behavior(root: Path) -> dict:
    result = {
        "scope": "static_functional_inference",
        "operations": [],
        "business_rules": [],
        "validations": [],
        "error_handling": [],
        "state_changes": [],
        "call_references": [],
        "limitations": [
            "Las reglas funcionales se infieren del código estático y no equivalen a requisitos confirmados.",
            "No se ejecutan funciones, consultas, tests ni llamadas externas.",
            "Las llamadas dinámicas, reflexión, inyección y configuración externa pueden quedar fuera del mapa.",
            "Los fragmentos de evidencia se limitan y redactan patrones comunes de secretos."
        ]
    }
    seen = set()
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if any(x in {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "vendor"} for x in parts):
            continue
        if path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".cs", ".php", ".rb"}:
            continue
        try:
            if path.stat().st_size > 1_000_000 or total + path.stat().st_size > 80_000_000:
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            total += path.stat().st_size
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        lines = source.splitlines()
        if path.suffix.lower() == ".py":
            try:
                tree = ast.parse(source)
            except SyntaxError:
                tree = None
            if tree:
                for node in ast.walk(tree):
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    start = node.lineno
                    end = getattr(node, "end_lineno", start)
                    body = ast.get_source_segment(source, node) or ""
                    body_lines = body.splitlines()
                    doc = ast.get_docstring(node) or ""
                    args = [x.arg for x in node.args.args]
                    returns = ast.unparse(node.returns) if node.returns else None
                    calls = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            fn = child.func
                            if isinstance(fn, ast.Name):
                                calls.append(fn.id)
                            elif isinstance(fn, ast.Attribute):
                                calls.append(fn.attr)
                    conditions = [f"{type(x.test).__name__} en línea {x.lineno}" for x in ast.walk(node) if isinstance(x, (ast.If, ast.While, ast.IfExp))]
                    raises = [ast.unparse(x.exc) if x.exc else "raise" for x in ast.walk(node) if isinstance(x, ast.Raise)]
                    handlers = [ast.unparse(x.type) if x.type else "exception genérica" for x in ast.walk(node) if isinstance(x, ast.ExceptHandler)]
                    validators = [x for x in calls if re.search(r"valid|check|assert|parse|schema|clean|sanitize", x, re.I)]
                    mutations = [x for x in calls if re.search(r"save|update|insert|delete|commit|add|remove|set|publish|send|write", x, re.I)]
                    item = {"name": node.name, "kind": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                            "file": rel, "start_line": start, "end_line": end, "parameters": args,
                            "return_type": returns, "docstring": doc[:500], "calls": sorted(set(calls))[:40],
                            "conditions": conditions[:30], "raises": raises[:20], "exception_handlers": handlers[:20],
                            "validation_calls": sorted(set(validators)), "possible_state_mutations": sorted(set(mutations)),
                            "confidence": "medium", "evidence": SECRET.sub(r"\1\2[REDACTED]", body[:900])}
                    key = (rel, start, node.name)
                    if key not in seen:
                        result["operations"].append(item); seen.add(key)
                    for call in sorted(set(calls)):
                        result["call_references"].append({"caller": node.name, "callee": call, "file": rel, "line": start, "confidence": "inferred"})
                    for condition in conditions:
                        result["business_rules"].append({"operation": node.name, "description": "Rama condicional detectada: " + condition, "file": rel, "line": start, "confidence": "inferred"})
                    for val in validators:
                        result["validations"].append({"operation": node.name, "validator": val, "file": rel, "line": start, "confidence": "inferred"})
                    for err in raises + handlers:
                        result["error_handling"].append({"operation": node.name, "error": err, "file": rel, "line": start, "confidence": "observed_static"})
                    for mutation in mutations:
                        result["state_changes"].append({"operation": node.name, "action_candidate": mutation, "file": rel, "line": start, "confidence": "inferred"})
        else:
            ext = path.suffix.lower()
            pattern = re.compile(r"(?:function\s+([A-Za-z_$][\w$]*)|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(?:public|private|protected)?\s*(?:static\s+)?[\w<>\[\]?]+\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{)")
            for n, line in enumerate(lines, 1):
                match = pattern.search(line)
                if match:
                    name = next((x for x in match.groups() if x), "anonymous")
                    key = (rel, n, name)
                    if key not in seen:
                        result["operations"].append({"name": name, "kind": "function_candidate", "file": rel,
                            "start_line": n, "end_line": n, "parameters": [], "return_type": None,
                            "docstring": "", "calls": [], "conditions": [], "raises": [],
                            "exception_handlers": [], "validation_calls": [], "possible_state_mutations": [],
                            "confidence": "low", "evidence": SECRET.sub(r"\1\2[REDACTED]", line.strip())[:900]})
                        seen.add(key)
                if re.search(r"\b(if|switch|case|throw|catch|validate|assert|save|update|insert|delete)\b", line, re.I):
                    category = "business_rules" if re.search(r"\b(if|switch|case)\b", line) else "error_handling" if re.search(r"\b(throw|catch)\b", line) else "validations" if re.search(r"\b(validate|assert)\b", line, re.I) else "state_changes"
                    result[category].append({"description": line.strip()[:240], "file": rel, "line": n, "confidence": "inferred"})
    for key in ("operations", "business_rules", "validations", "error_handling", "state_changes", "call_references"):
        result[key] = result[key][:5000]
    result["summary"] = {key: len(result[key]) for key in ("operations", "business_rules", "validations", "error_handling", "state_changes", "call_references")}
    return result

def build_analysis_html(name: str, analysis: dict) -> str:
    def esc(value):
        return html.escape(str(value if value is not None else ""), quote=True)

    deep = analysis.get("deep_analysis", {})
    functional = analysis.get("functional_analysis", {})
    quality = analysis.get("quality_analysis", {})
    stats = deep.get("scan_stats", {})
    findings = quality.get("bug_candidates", [])[:500]
    summary = functional.get("summary", {})
    categories = [
        ("operations", "Operaciones y funciones"),
        ("business_rules", "Reglas y ramas de negocio"),
        ("validations", "Validaciones"),
        ("error_handling", "Gestión de errores"),
        ("state_changes", "Cambios de estado y efectos"),
        ("call_references", "Referencias de llamadas"),
    ]

    def json_block(value):
        return esc(json.dumps(value, ensure_ascii=False, indent=2))

    def render_findings():
        if not findings:
            return "<div class='empty'>No se han detectado candidatos de bug. El análisis estático puede tener falsos negativos.</div>"
        cards = []
        for i, finding in enumerate(findings, 1):
            severity = str(finding.get("severity", "low")).lower()
            severity_label = {"high": "Alta", "medium": "Media", "low": "Baja"}.get(severity, severity.title())
            location = str(finding.get("file", "N/D")) + ":" + str(finding.get("line", "N/D"))
            searchable = " ".join(str(finding.get(k, "")) for k in ("severity", "title", "file", "description", "excerpt")).lower()
            locations = finding.get("occurrences", [])
            locations_html = "<details class='occurrences'><summary>Ver " + str(len(locations)) + " ubicaciones agrupadas</summary><ul>" + "".join("<li><code>" + esc(x.get("file", "")) + ":" + esc(x.get("line", "")) + "</code><pre>" + esc(x.get("excerpt", "")) + "</pre></li>" for x in locations) + "</ul></details>" if locations else ""
            cards.append(
                "<article class='finding' data-severity='" + esc(severity) + "' data-search='" + esc(searchable) + "'>"
                "<div class='finding-top'><span class='severity " + esc(severity) + "'>" + esc(severity_label) + "</span><span class='finding-number'>#" + str(i) + "</span></div>"
                "<h3>" + esc(finding.get("title", "Posible bug")) + "</h3>"
                "<p class='location'><span>Ubicación</span><code>" + esc(location) + "</code></p>"
                "<p>" + esc(finding.get("description", "")) + "</p><p class='occurrence-badge'>" + str(finding.get("occurrence_count", 1)) + " coincidencias del mismo patrón</p>" + locations_html +
                "<details><summary>Ver evidencia de código</summary><pre>" + esc(finding.get("excerpt", "")) + "</pre></details></article>"
            )
        return "".join(cards)

    def render_table(items, key):
        if not items:
            return "<div class='empty'>No hay elementos detectados en este apartado.</div>"
        rows = []
        for item in items:
            detail = item.get("evidence") or item.get("description") or item.get("error") or item.get("validator") or item.get("action_candidate") or item.get("callee") or ""
            label = item.get("name") or item.get("operation") or item.get("caller") or item.get("validator") or item.get("action_candidate") or item.get("callee") or "Detección"
            line = item.get("start_line") or item.get("line")
            location = str(item.get("file", "")) + ((":" + str(line)) if line else "")
            confidence = item.get("confidence", "")
            rows.append("<tr><td>" + esc(label) + "</td><td><code>" + esc(location) + "</code></td><td>" + esc(confidence) + "</td><td><pre>" + esc(detail) + "</pre></td></tr>")
        return "<div class='table-wrap'><table><thead><tr><th>Elemento</th><th>Ubicación</th><th>Confianza</th><th>Evidencia / detalle</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"

    sections = []
    sections.append("<header class='hero'><div class='hero-inner'><div class='eyebrow'>Análisis estático · Informe técnico</div><h1>" + esc(name) + "</h1><p>Informe de código, calidad y comportamiento inferido. Los hallazgos son señales que requieren revisión, no defectos confirmados.</p><div class='hero-meta'><span>Archivos inspeccionados: " + esc(stats.get("files_seen", "N/D")) + "</span><span>Tests detectados: " + esc(stats.get("test_files", "N/D")) + "</span><span>Candidatos de bug: " + str(len(findings)) + "</span><span>Validación runtime: no realizada</span></div></div></header>")
    sections.append("<nav class='report-nav' aria-label='Navegación del informe'><div class='report-nav-inner'>" + "".join("<a href='#" + anchor + "'>" + label + "</a>" for anchor, label in [("summary","Resumen"),("findings","Posibles bugs"),("test-findings","Tests"),("functional","Análisis funcional"),("architecture","Arquitectura y API"),("security","Seguridad"),("limitations","Limitaciones")]) + "</div></nav>")
    sections.append("<main><section id='summary' class='summary'><div class='section-kicker'>Resumen</div><div class='metrics'>" +
        "".join("<div class='metric'><strong>" + esc(value) + "</strong><span>" + esc(label) + "</span></div>" for value, label in [
            (stats.get("files_seen", "N/D"), "Archivos inspeccionados"),
            (stats.get("text_bytes_read", "N/D"), "Bytes leídos"),
            (stats.get("routes", "N/D"), "Rutas detectadas"),
            (stats.get("python_functions", "N/D"), "Funciones Python"),
            (stats.get("python_classes", "N/D"), "Clases Python"),
            (stats.get("test_files", "N/D"), "Ficheros de test"),
            (len(findings), "Posibles bugs"),
            (summary.get("operations", 0), "Operaciones inferidas"),
        ]) + "</div><details class='raw-summary'><summary>Ver resumen técnico original</summary><pre>" + json_block(stats) + "</pre></details></section>")
    sections.append("<section id='findings'><div class='section-kicker'>Calidad · Revisión priorizada</div><h2>Posibles bugs detectados</h2><p class='section-intro'>Cada señal incluye ubicación y evidencia. Confirma el contexto antes de modificar el código.</p><div class='filter-bar'><input id='finding-search' type='search' placeholder='Buscar por texto, archivo o descripción…'><select id='severity-filter'><option value='all'>Todas las prioridades</option><option value='high'>Alta</option><option value='medium'>Media</option><option value='low'>Baja</option></select><span id='finding-count'>" + str(len(findings)) + " hallazgos</span></div><div class='finding-grid'>" + render_findings() + "</div></section>")
    test_findings = quality.get("test_bug_candidates", [])
    test_cards = "".join("<li><b>" + esc(x.get("code", "")) + " · " + esc(x.get("title", "")) + "</b> — " + str(x.get("occurrence_count", len(x.get("occurrences", [])))) + " coincidencias<ul>" + "".join("<li><code>" + esc(loc.get("file", "")) + ":" + esc(loc.get("line", "")) + "</code><pre>" + esc(loc.get("excerpt", "")) + "</pre></li>" for loc in x.get("occurrences", [])) + "</ul></li>" for x in test_findings)
    sections.append("<section id='test-findings'><details><summary>Detecciones encontradas en tests (separadas de producción) <span class='count'>" + str(len(test_findings)) + " grupos</span></summary><p class='section-intro'>No se contabilizan como bugs de producción ni afectan a la puntuación.</p><ul>" + test_cards + "</ul></details></section>")
    sections.append("<section id='functional'><div class='section-kicker'>Comportamiento inferido</div><h2>Análisis funcional</h2><div class='metrics'>" + "".join("<div class='metric'><strong>" + esc(summary.get(key, 0)) + "</strong><span>" + esc(label) + "</span></div>" for key, label in [("operations","Operaciones"),("business_rules","Reglas / ramas"),("validations","Validaciones"),("error_handling","Errores"),("state_changes","Cambios de estado"),("call_references","Referencias")]) + "</div><details class='raw-summary'><summary>Ver resumen funcional original</summary><pre>" + json_block(summary) + "</pre></details>")
    for key, title in categories:
        items = functional.get(key, [])
        sections.append("<details class='data-section'><summary>" + esc(title) + "<span class='count'>" + str(len(items)) + "</span></summary>" + render_table(items, key) + "</details>")
    sections.append("</section>")
    architecture = {"architecture": deep.get("architecture", {}), "api": deep.get("api", {}), "dependencies": deep.get("dependencies", {}), "data": deep.get("data", {})}
    sections.append("<section id='architecture'><div class='section-kicker'>Estructura</div><h2>Arquitectura y API detectadas</h2><pre class='json'>" + json_block(architecture) + "</pre></section>")
    security_data = {"security": deep.get("security", {}), "integrations": deep.get("integrations", {}), "configuration": deep.get("configuration", {})}
    sections.append("<section id='security'><div class='section-kicker'>Seguridad e integraciones</div><h2>Seguridad, integraciones y configuración</h2><pre class='json'>" + json_block(security_data) + "</pre></section>")
    limitations = functional.get("limitations", []) + deep.get("limitations", [])
    sections.append("<section id='limitations'><div class='section-kicker'>Contexto</div><h2>Limitaciones</h2><ul class='limitations'>" + "".join("<li>" + esc(x) + "</li>" for x in limitations) + "</ul></section>")
    html_doc = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>Informe de análisis · """ + esc(name) + """</title>""" + stylesheet_link() + """</head><body>""" + "".join(sections) + """</main><script>
(function(){const cards=[...document.querySelectorAll('.finding')],search=document.getElementById('finding-search'),filter=document.getElementById('severity-filter'),count=document.getElementById('finding-count');function apply(){const q=(search.value||'').toLowerCase(),s=filter.value;let n=0;cards.forEach(c=>{const show=(!q||(c.dataset.search||'').includes(q))&&(s==='all'||c.dataset.severity===s);c.hidden=!show;if(show)n++});count.textContent=n+' hallazgos visibles de '+cards.length}search.addEventListener('input',apply);filter.addEventListener('change',apply)})();
</script></body></html>"""
    return html_doc
