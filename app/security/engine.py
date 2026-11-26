"""Repository-level security/correctness scan: Python + Java engines and config files."""
from __future__ import annotations

import re
import time
from pathlib import Path

from .contracts import SCHEMA_VERSION, SecurityFinding
from .java_engine import JAVA_AVAILABLE, JavaProject
from .python_engine import PythonProject, find_token_secrets, looks_like_secret, redact

SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "dist", "build", "target", "vendor",
             "reports", "workspaces", "logs", ".gradle", ".idea", ".mvn", "site-packages", "generated", "generated-sources"}
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 80_000_000
CONFIG_NAME = re.compile(r"(^|/)(application|bootstrap)[^/]*\.(properties|ya?ml)$|(^|/)\.env(\.[^/]*)?$|"
                         r"(^|/)docker-compose[^/]*\.ya?ml$|\.properties$", re.I)
TEST_PATH = re.compile(r"(^|/)(src/test|tests?|testing|spec|specs|__tests__|test-data|fixtures?)(/|$)|"
                       r"(^|/)(test_[^/]*|[^/]*_test\.py|[^/]*Tests?\.java|[^/]*IT\.java|conftest\.py)$", re.I)
I18N_BUNDLE = re.compile(r"(^|/)(messages|labels|i18n|lang|locale)[^/]*\.properties$|(^|/)i18n/|"
                         r"_[a-z]{2}(_[A-Z]{2})?\.properties$")
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}


def is_test_path(rel: str) -> bool:
    return bool(TEST_PATH.search(rel))


def _iter_files(root: Path):
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts[:-1]):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_FILE_BYTES or total + size > MAX_TOTAL_BYTES:
            yield path, None, "omitido por tamaño"
            continue
        total += size
        yield path, size, None


def scan_config(text: str, rel: str, is_test: bool) -> list[SecurityFinding]:
    findings = []
    lines = text.splitlines()
    for index, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith(("#", "!", "//")):
            continue
        match = re.match(r"^([\w.\-\[\]]+)\s*[:=]\s*(.*)$", line)
        if not match:
            label = find_token_secrets(line)
            if label:
                findings.append(SecurityFinding("SEC-SECRET", rel, index, redact(line, line), f"El fichero contiene un/a {label}.",
                                                "config", "high", is_test=is_test))
            continue
        key, value = match.group(1), match.group(2).strip().strip('"').strip("'")
        lower_key = key.lower()
        context = " ".join(l.strip() for l in lines[max(0, index - 6):index]).lower()
        def add(rule_id, message, severity=None, confidence="high", snippet=None):
            findings.append(SecurityFinding(rule_id, rel, index, snippet or line, message, "config", confidence,
                                            severity=severity, is_test=is_test))
        if (lower_key.endswith("exposure.include") or (lower_key == "include" and "exposure" in context)) and value == "*":
            add("SEC-DEBUG", "Todos los endpoints de Actuator expuestos (incluye env, heapdump, etc.).")
        elif lower_key.endswith("h2.console.enabled") or (lower_key == "enabled" and "console" in context and "h2" in context):
            if value.lower() == "true":
                add("SEC-DEBUG", "Consola H2 habilitada (acceso SQL desde el navegador).")
        elif lower_key.endswith("include-stacktrace") and value.lower() == "always":
            add("SEC-DEBUG", "Las respuestas de error incluyen la traza completa.", severity="low")
        elif lower_key in ("debug",) and value.lower() == "true":
            add("SEC-DEBUG", "Modo debug activado en la configuración.", severity="low")
        label = find_token_secrets(value)
        if label:
            add("SEC-SECRET", f"La configuración contiene un/a {label}.", snippet=redact(line, value))
        elif value and not value.startswith(("${", "#{", "{{", "ENC(", "vault:", "{cipher}")) and \
                looks_like_secret(key.replace(".", "_").replace("-", "_"), value):
            add("SEC-SECRET", f"'{key}' tiene un valor literal que parece una credencial.", confidence="medium",
                snippet=redact(line, value))
    return findings


def scan_repository(root: Path) -> dict:
    """Run every engine on ``root`` and return a JSON-serialisable result."""
    started = time.monotonic()
    root = Path(root)
    findings: list[SecurityFinding] = []
    coverage = {"python": 0, "java": 0, "config": 0, "skipped": [], "parse_errors": [], "unsupported": {}}
    java = JavaProject() if JAVA_AVAILABLE else None
    python = PythonProject()
    for path, size, skipped in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        relevant = suffix in (".py", ".java") or CONFIG_NAME.search(rel)
        if skipped:
            if relevant:
                coverage["skipped"].append({"file": rel, "reason": skipped})
            continue
        if not relevant:
            if suffix in (".js", ".ts", ".jsx", ".tsx", ".kt", ".go", ".cs", ".php", ".rb"):
                coverage["unsupported"][suffix] = coverage["unsupported"].get(suffix, 0) + 1
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            coverage["skipped"].append({"file": rel, "reason": str(exc)})
            continue
        test = is_test_path(rel)
        if suffix == ".py":
            python.add(text, rel, test)
            coverage["python"] += 1
        elif suffix == ".java":
            if java is None:
                coverage["unsupported"][".java (tree-sitter no instalado)"] = coverage["unsupported"].get(
                    ".java (tree-sitter no instalado)", 0) + 1
                continue
            java.add(text, rel, test)
            coverage["java"] += 1
        else:
            if I18N_BUNDLE.search(rel):
                continue  # translation bundles hold UI labels ("password=Contraseña"), not configuration
            findings.extend(scan_config(text, rel, test))
            coverage["config"] += 1
    python_findings, python_errors = python.run()
    findings.extend(python_findings)
    coverage["parse_errors"].extend(python_errors)
    if java is not None and java.files:
        findings.extend(java.run())
        coverage["parse_errors"].extend(java.errors)
    unique: dict[str, SecurityFinding] = {}
    for finding in findings:
        unique.setdefault(f"{finding.rule_id}|{finding.file}|{finding.line}", finding)
    ordered = sorted(unique.values(), key=lambda f: (
        f.is_test, SEVERITY_ORDER.get(f.severity or f.rule.severity, 3), CONFIDENCE_ORDER.get(f.confidence, 3), f.file, f.line))
    items = [f.to_dict() for f in ordered]
    production = [f for f in items if not f["is_test"]]
    by_rule: dict[str, int] = {}
    by_owasp: dict[str, int] = {}
    for item in production:
        by_rule[item["rule_id"]] = by_rule.get(item["rule_id"], 0) + 1
        if item.get("owasp"):
            by_owasp[item["owasp"]["id"]] = by_owasp.get(item["owasp"]["id"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "engine": "minagent-static",
        "java_profile": "tree-sitter" if JAVA_AVAILABLE else "no disponible (instalar tree-sitter y tree-sitter-java)",
        "findings": items,
        "summary": {
            "total": len(production),
            "tests": len(items) - len(production),
            "high": sum(1 for f in production if f["severity"] == "high"),
            "medium": sum(1 for f in production if f["severity"] == "medium"),
            "low": sum(1 for f in production if f["severity"] == "low"),
            "security": sum(1 for f in production if f["category"] == "security"),
            "bugs": sum(1 for f in production if f["category"] == "bug"),
            "dataflow": sum(1 for f in production if f["trace"]),
            "by_rule": by_rule,
            "by_owasp": dict(sorted(by_owasp.items())),
        },
        "coverage": {**coverage, "skipped": coverage["skipped"][:200], "parse_errors": coverage["parse_errors"][:200]},
        "duration_ms": int((time.monotonic() - started) * 1000),
        "limitations": [
            "Análisis estático: no se ejecuta el código; un hallazgo es un candidato con evidencia, no una explotación probada.",
            "El flujo de datos es intraprocedural con resúmenes de métodos; en Java los resúmenes se asocian por "
            "nombre y número de argumentos, por lo que los métodos homónimos se tratan juntos (confianza media).",
            "Fuentes reconocidas: Flask, Django/DRF, FastAPI, Spring MVC/WebFlux, Servlet, JAX-RS y listeners de "
            "Kafka/RabbitMQ/JMS. Otras entradas (ficheros, colas propias) no se consideran no confiables.",
            "No se analizan JavaScript/TypeScript, Kotlin, Go, C# ni PHP con este motor.",
        ],
    }
