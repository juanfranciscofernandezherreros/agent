"""Heuristic quality scoring and bug-pattern detection for static repository analysis.

Findings are review candidates, not confirmed runtime defects.
"""
from pathlib import Path
import re

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "target", "vendor"}
SOURCE_SUFFIXES = {".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".go", ".cs", ".php", ".rb"}

PATTERNS = [
    ("BUG001", "high", "Captura de excepción ignorada", re.compile(r"\bexcept\b[^:\n]*:\s*(?:pass|\.\.\.)\s*(?:#.*)?$", re.I), "La excepción puede ocultar un fallo y dejar el proceso en un estado inconsistente."),
    ("BUG002", "high", "Comparación sospechosa con None/null", re.compile(r"(?<![=!<>])==\s*None\b|\bnull\s*==\s*\w+", re.I), "Revisar la semántica de la comparación y si el valor puede ser nulo."),
    ("BUG003", "medium", "Bloque TODO/FIXME pendiente", re.compile(r"\b(TODO|FIXME|XXX|HACK)\b", re.I), "Hay una tarea o deuda técnica anotada en el código."),
    ("BUG004", "high", "Uso de assert en código de aplicación", re.compile(r"^\s*assert\s+"), "Las aserciones pueden desactivarse en ejecución optimizada; no deberían sustituir validaciones de entrada."),
    ("BUG005", "medium", "Comparación de igualdad potencialmente incorrecta", re.compile(r"\b(?:if|while)\s+\w+\s+is\s+['\"]|\b(?:if|while)\s+['\"][^'\"]+['\"]\s+is\s+\w+", re.I), "En Python, 'is' compara identidad, no igualdad de valores."),
    ("BUG006", "high", "Credencial literal en código", re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[=:]\s*['\"][^'\"]{6,}['\"]"), "Posible secreto codificado directamente. Verificar que no sea un placeholder o dato de prueba."),
]

WEIGHTS = {"high": 12, "medium": 5, "low": 2}


def analyze_quality(root: Path, deep: dict, functional: dict, java: dict) -> dict:
    findings = []
    files_scanned = 0
    total_bytes = 0
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
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
        for line_no, line in enumerate(source.splitlines(), 1):
            for code, severity, title, pattern, explanation in PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "code": code, "severity": severity, "title": title,
                        "file": rel, "line": line_no,
                        "excerpt": line.strip()[:300], "description": explanation,
                        "confidence": "heuristic_candidate",
                    })
                    break

    tests = deep.get("tests", {}).get("files", [])
    parse_issues = deep.get("parse_issues", [])
    security = deep.get("security", {})
    security_count = sum(len(v) for v in security.values() if isinstance(v, list))
    high = sum(x["severity"] == "high" for x in findings)
    medium = sum(x["severity"] == "medium" for x in findings)
    # Transparent, capped deductions. A score is a prioritisation indicator, not a defect probability.
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
            "security_indicators": security_count,
            "deductions": min(80, deductions),
        },
        "bug_candidates": findings[:2000],
        "summary": {
            "bug_candidates": len(findings), "high": high, "medium": medium,
            "files_scanned": files_scanned, "test_files": len(tests),
        },
        "limitations": [
            "La puntuación es un indicador heurístico de priorización, no una medida objetiva de calidad ni una probabilidad de defectos.",
            "Los patrones detectan candidatos que requieren revisión humana; pueden producir falsos positivos y falsos negativos.",
            "No se ejecutan compiladores, analizadores semánticos, pruebas ni servicios; no se confirma ningún bug en runtime.",
            "La falta de tests detectados puede deberse a convenciones o ubicaciones no reconocidas."
        ],
    }
