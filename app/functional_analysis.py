from pathlib import Path
import ast
import html
import json
import re

SECRET = re.compile(r"(?i)(password|secret|token|api[_-]?key|private[_-]?key)(\\s*[=:]\\s*)[^\\s,;]+")

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
                            "confidence": "medium", "evidence": SECRET.sub(r"\\1\\2[REDACTED]", body[:900])}
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
            pattern = re.compile(r"(?:function\\s+([A-Za-z_$][\\w$]*)|(?:const|let|var)\\s+([A-Za-z_$][\\w$]*)\\s*=\\s*(?:async\\s*)?\\([^)]*\\)\\s*=>|(?:public|private|protected)?\\s*(?:static\\s+)?[\\w<>\\[\\]?]+\\s+([A-Za-z_$][\\w$]*)\\s*\\([^)]*\\)\\s*\\{)")
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
                            "confidence": "low", "evidence": SECRET.sub(r"\\1\\2[REDACTED]", line.strip())[:900]})
                        seen.add(key)
                if re.search(r"\\b(if|switch|case|throw|catch|validate|assert|save|update|insert|delete)\\b", line, re.I):
                    category = "business_rules" if re.search(r"\\b(if|switch|case)\\b", line) else "error_handling" if re.search(r"\\b(throw|catch)\\b", line) else "validations" if re.search(r"\\b(validate|assert)\\b", line, re.I) else "state_changes"
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
    sections = []
    sections.append("<h1>Análisis del microservicio: " + esc(name) + "</h1>")
    sections.append("<p>Informe generado mediante análisis estático. No implica validación del comportamiento en ejecución.</p>")
    sections.append("<h2>Resumen</h2><pre>" + esc(json.dumps(deep.get("scan_stats", {}), ensure_ascii=False, indent=2)) + "</pre>")
    sections.append("<h2>Análisis funcional</h2>")
    summary = functional.get("summary", {})
    sections.append("<pre>" + esc(json.dumps(summary, ensure_ascii=False, indent=2)) + "</pre>")
    for key, title in [("operations","Operaciones y funciones"),("business_rules","Reglas y ramas de negocio"),("validations","Validaciones"),("error_handling","Gestión de errores"),("state_changes","Cambios de estado y efectos"),("call_references","Referencias de llamadas")]:
        sections.append("<h3>" + title + "</h3><table><thead><tr><th>Elemento</th><th>Ubicación</th><th>Confianza</th><th>Evidencia / detalle</th></tr></thead><tbody>")
        for item in functional.get(key, []):
            detail = item.get("evidence") or item.get("description") or item.get("error") or item.get("validator") or item.get("action_candidate") or item.get("callee") or ""
            label = item.get("name") or item.get("operation") or item.get("caller") or item.get("validator") or item.get("action_candidate") or item.get("callee") or "Detección"
            loc = item.get("file", "") + (":" + str(item.get("start_line") or item.get("line")) if item.get("start_line") or item.get("line") else "")
            sections.append("<tr><td>" + esc(label) + "</td><td>" + esc(loc) + "</td><td>" + esc(item.get("confidence","")) + "</td><td><pre>" + esc(detail) + "</pre></td></tr>")
        sections.append("</tbody></table>")
    sections.append("<h2>Arquitectura y API detectadas</h2><pre>" + esc(json.dumps({"architecture":deep.get("architecture",{}),"api":deep.get("api",{}),"dependencies":deep.get("dependencies",{}),"data":deep.get("data",{})},ensure_ascii=False,indent=2)) + "</pre>")
    sections.append("<h2>Seguridad e integraciones</h2><pre>" + esc(json.dumps({"security":deep.get("security",{}),"integrations":deep.get("integrations",{}),"configuration":deep.get("configuration",{})},ensure_ascii=False,indent=2)) + "</pre>")
    limitations = functional.get("limitations", []) + deep.get("limitations", [])
    sections.append("<h2>Limitaciones</h2><ul>" + "".join("<li>"+esc(x)+"</li>" for x in limitations) + "</ul>")
    return "<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Analisis - "+esc(name)+"</title><style>body{font:15px/1.55 system-ui,sans-serif;max-width:1200px;margin:36px auto;padding:0 20px;color:#202938}h1,h2,h3{line-height:1.2}table{width:100%;border-collapse:collapse;margin:12px 0 28px;font-size:13px}th,td{border:1px solid #d8dee8;padding:8px;text-align:left;vertical-align:top}th{background:#eef2f7}pre{white-space:pre-wrap;overflow-wrap:anywhere;margin:0}tr:nth-child(even){background:#fafbfd}</style></head><body>"+"".join(sections)+"</body></html>"
