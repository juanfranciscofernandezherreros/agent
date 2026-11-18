"""Heuristic quality scoring and bug-pattern detection for static repository analysis.

Findings are review candidates, not confirmed runtime defects.
"""
from pathlib import Path
import re

from app.security.owasp import OWASP_SQL_INJECTION

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "target", "vendor", "reports", "workspaces", "logs"}
SOURCE_SUFFIXES = {".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".go", ".cs", ".php", ".rb"}

PATTERNS = [
    ("BUG001", "high", "Captura de excepción ignorada", re.compile(r"\bexcept\b[^:\n]*:\s*(?:pass|\.\.\.)\s*(?:#.*)?$", re.I), "La excepción puede ocultar un fallo y dejar el proceso en un estado inconsistente."),
    ("BUG002", "high", "Comparación sospechosa con None/null", re.compile(r"(?<![=!<>])==\s*None\b|\bnull\s*==\s*\w+", re.I), "Revisar la semántica de la comparación y si el valor puede ser nulo."),
    ("BUG003", "medium", "Bloque TODO/FIXME pendiente", re.compile(r"\b(TODO|FIXME|XXX|HACK)\b", re.I), "Hay una tarea o deuda técnica anotada en el código."),
    ("BUG004", "high", "Uso de assert en código de aplicación", re.compile(r"^\s*assert\s+"), "Las aserciones pueden desactivarse en ejecución optimizada; no deberían sustituir validaciones de entrada."),
    ("BUG005", "medium", "Comparación de igualdad potencialmente incorrecta", re.compile(r"\b(?:if|while)\s+\w+\s+is\s+['\"]|\b(?:if|while)\s+['\"][^'\"]+['\"]\s+is\s+\w+", re.I), "En Python, 'is' compara identidad, no igualdad de valores."),
    ("BUG006", "high", "Credencial literal en código", re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[=:]\s*['\"][^'\"]{6,}['\"]"), "Posible secreto codificado directamente. Verificar que no sea un placeholder o dato de prueba."),
    ("BUG007", "high", "Captura genérica de excepción", re.compile(r"(?m)^\s*except\s*:\s*(?:#.*)?$"), "La captura sin tipo puede ocultar errores inesperados y continuar en un estado inválido."),
    ("BUG008", "medium", "Argumento mutable por defecto", re.compile(r"(?m)^\s*def\s+\w+\s*\([^)]*=\s*(?:\[\]|\{\}|set\(\))"), "Un valor mutable por defecto se comparte entre llamadas y puede conservar estado accidentalmente."),
    ("BUG009", "high", "Uso de eval/exec", re.compile(r"\b(?:eval|exec)\s*\("), "Evalúa código dinámico; puede producir ejecución no prevista o vulnerabilidad si recibe datos externos."),
    ("BUG010", "medium", "Comparación explícita con booleano", re.compile(r"\b(?:if|while)\s+[^:]+\s+==\s+(?:True|False)\b"), "La comparación explícita puede ser redundante o indicar una condición incorrecta; validar la intención."),
    ("BUG011", "high", "SQL con interpolación o concatenación", re.compile(r"(?i)\b(?:select|insert\s+into|update|delete\s+from)\b.{0,180}(?:\+\s*\w+|f['\"]|%s|\.format\()"), "SQL construido dinámicamente; revisar si los valores se parametrizan para evitar errores de contrato e inyección."),
]

WEIGHTS = {"high": 12, "medium": 5, "low": 2}


SQL_KEYWORDS = re.compile(r"(?i)\b(?:select|insert\s+into|update\s+\w+\s+set|delete\s+from)\b")
SQL_DYNAMIC = [
    re.compile(r"(?i)\b(?:select|insert\s+into|update|delete\s+from)\b.{0,250}\+\s*(?:\w+|[\"'][^\"']*[\"'])"),
    re.compile(r"(?i)\bf[\"'].*(?:select|insert|update|delete).*\{[^}]+\}"),
    re.compile(r"(?i)\b(?:select|insert|update|delete)\b.{0,250}(?:\.format\s*\(|%\s*(?:\w+|\())"),
    re.compile(r"(?i)\b(?:select|insert|update|delete)\b.{0,250}\$\{[^}]+\}"),
]

def _analyze_sql_injection(source: str, rel: str) -> list[dict]:
    """Detect suspicious dynamic SQL construction; candidates require manual validation."""
    hits = []
    for line_no, line in enumerate(source.splitlines(), 1):
        if not SQL_KEYWORDS.search(line):
            continue
        if any(pattern.search(line) for pattern in SQL_DYNAMIC):
            hits.append({
                "file": rel, "line": line_no, "excerpt": line.strip()[:300],
                "reason": "SQL statement appears to include dynamic interpolation, formatting or concatenation.",
            })
    if not hits:
        return []
    return [{
        "code": "SQLI001",
        "severity": "high",
        "title": "Posible SQL Injection por SQL dinámico",
        "description": "Se detectó construcción dinámica de una sentencia SQL. Comprobar si los valores externos se incorporan sin parametrización y si existe un flujo alcanzable hasta la consulta.",
        "confidence": "heuristic_candidate",
        "cwe": dict(OWASP_SQL_INJECTION["cwe"]),
        "owasp": dict(OWASP_SQL_INJECTION["owasp_top10"]),
        "asvs_area": OWASP_SQL_INJECTION["asvs_area"],
        "owasp_guidance": list(OWASP_SQL_INJECTION["guidance"]),
        "references": list(OWASP_SQL_INJECTION["references"]),
        "occurrences": hits,
        "occurrence_count": len(hits),
        "file": hits[0]["file"], "line": hits[0]["line"], "excerpt": hits[0]["excerpt"],
        "recommended_action": "Revisar el flujo de datos y sustituir la concatenación/interpolación por consultas parametrizadas; validar con evidencia antes de confirmar.",
    }]


def analyze_quality(root: Path, deep: dict, functional: dict, java: dict) -> dict:
    grouped = {}
    files_scanned = 0
    total_bytes = 0
    test_hits = []
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        try:
            size = path.stat().st_size
            if size > 1_000_000 or total_bytes + size > 80_000_000:
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            total_bytes += size
            files_scanned += 1
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        is_test = any(part.lower() in {"test", "tests", "testing", "spec", "specs"} for part in parts) or bool(re.search(r"(^|[/\\])test[^/\\]*|[^/\\]*test[^/\\]*$", rel, re.I))
        bucket = "tests" if is_test else "production"
        for line_no, line in enumerate(source.splitlines(), 1):
            for code, severity, title, pattern, explanation in PATTERNS:
                if pattern.search(line):
                    occurrence = {"file": rel, "line": line_no, "excerpt": line.strip()[:300]}
                    if is_test:
                        test_hits.append({"code": code, "severity": severity, "title": title, "description": explanation, "occurrences": [occurrence]})
                    else:
                        key = (code, title)
                        if key not in grouped:
                            grouped[key] = {"code": code, "severity": severity, "title": title, "description": explanation, "confidence": "heuristic_candidate", "occurrences": []}
                        grouped[key]["occurrences"].append(occurrence)
                    break

    findings = list(grouped.values())
    # SQL Injection gets a dedicated security finding with CWE/OWASP metadata.
    sql_injection_findings = []
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        is_test = any(part.lower() in {"test", "tests", "testing", "spec", "specs"} for part in parts) or bool(re.search(r"(^|[/\\])test[^/\\]*|[^/\\]*test[^/\\]*$", rel, re.I))
        candidates = _analyze_sql_injection(source, rel)
        if is_test:
            test_hits.extend(candidates)
        else:
            sql_injection_findings.extend(candidates)
    findings.extend(sql_injection_findings)
    for item in findings:
        item["occurrence_count"] = len(item["occurrences"])
        first = item["occurrences"][0]
        item["file"], item["line"], item["excerpt"] = first["file"], first["line"], first["excerpt"]
    tests = deep.get("tests", {}).get("files", [])
    parse_issues = deep.get("parse_issues", [])
    security = deep.get("security", {})
    security_count = sum(len(v) for v in security.values() if isinstance(v, list))
    high = sum(x["severity"] == "high" for x in findings)
    medium = sum(x["severity"] == "medium" for x in findings)
    test_groups = {}
    for hit in test_hits:
        key = (hit["code"], hit["title"])
        if key not in test_groups:
            test_groups[key] = {**{k: hit[k] for k in ("code", "severity", "title", "description")}, "occurrences": []}
        test_groups[key]["occurrences"].extend(hit["occurrences"])
    test_candidates = list(test_groups.values())
    for item in test_candidates:
        item["occurrence_count"] = len(item["occurrences"])
        first = item["occurrences"][0]
        item["file"], item["line"], item["excerpt"] = first["file"], first["line"], first["excerpt"]
    # Score production-pattern groups, not every repeated line occurrence.
    deductions = min(45, high * 12 + medium * 5)
    if not tests:
        deductions += 10
    if parse_issues:
        deductions += min(10, len(parse_issues) * 2)
    if security_count:
        deductions += min(15, security_count * 3)
    score = max(0, 100 - min(80, deductions))
    return {
        "score": score,
        "rating": "Bueno" if score >= 85 else "Mejorable" if score >= 70 else "Requiere atención",
        "score_type": "heuristic_static_quality",
        "score_factors": {
            "bug_candidates_high": high, "bug_candidates_medium": medium,
            "test_files_detected": len(tests), "parse_issues": len(parse_issues),
            "security_indicators": security_count, "deductions": min(80, deductions),
        },
        "bug_candidates": findings[:2000],
        "test_bug_candidates": test_candidates[:2000],
        "summary": {
            "bug_candidates": len(findings), "bug_occurrences": sum(x["occurrence_count"] for x in findings),
            "test_bug_groups": len(test_candidates), "test_bug_occurrences": sum(x["occurrence_count"] for x in test_candidates),
            "high": high, "medium": medium, "files_scanned": files_scanned, "test_files": len(tests),
        },
        "limitations": [
            "Las detecciones se agrupan por patrón/código: cada grupo muestra sus ubicaciones; el total de ocurrencias se conserva.",
            "Los hallazgos de tests se separan de los candidatos encontrados en código de producción.",
            "La puntuación cuenta grupos de patrones en producción, no cada repetición.",
            "La puntuación es un indicador heurístico de priorización, no una medida objetiva de calidad ni una probabilidad de defectos.",
            "Los patrones pueden producir falsos positivos y falsos negativos; no se ejecutan compiladores, pruebas ni servicios.",
            "La falta de tests detectados puede deberse a convenciones o ubicaciones no reconocidas.",
        ],
    }
