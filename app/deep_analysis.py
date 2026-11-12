from pathlib import Path
import ast
import json
import re

SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "vendor"}
TEXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".cs", ".php", ".rb", ".kt", ".swift", ".sql", ".yaml", ".yml", ".json", ".toml", ".xml", ".md", ".txt", ".ini", ".cfg", ".sh", ".ps1", ".tf", ".graphql", ".proto"}
ROUTES = [
    ("FastAPI", re.compile(r"@(app|router)\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)")),
    ("Express", re.compile(r"(app|router)\.(get|post|put|patch|delete)\s*\(\s*['\x60]([^'\x60]+)")),
    ("Flask", re.compile(r"@\w+\.route\s*\(\s*['\"]([^'\"]+)")),
]
SECURITY = {
    "auth": r"(?i)\b(jwt|oauth|openid|authenticate|authentication|passport)\b",
    "authorization": r"(?i)\b(permissions?|roles?|rbac|authorize|acl)\b",
    "crypto": r"(?i)\b(bcrypt|argon2|scrypt|encrypt|decrypt|crypto)\b",
    "validation": r"(?i)\b(pydantic|zod|joi|yup|marshmallow|validator)\b",
    "cors_rate_limit": r"(?i)(cors|rate.?limit|throttl)",
}
INTEGRATIONS = {
    "http": r"(?i)\b(requests\.|httpx\.|axios\.|fetch\(|urllib)",
    "database": r"(?i)\b(sqlalchemy|psycopg|asyncpg|mysql|mongoose|prisma|sequelize|sqlite|mongodb|redis)\b",
    "messaging": r"(?i)\b(kafka|rabbitmq|celery|dramatiq|bullmq|sqs|pubsub|nats|amqp)\b",
    "cloud": r"(?i)\b(boto3|s3|gcs|azure|aws|google\.cloud)\b",
    "payments_email": r"(?i)\b(stripe|paypal|sendgrid|mailgun|postmark|smtp)\b",
}
SECRET = re.compile(r"(?i)(password|secret|token|api[_-]?key|private[_-]?key)(\s*[=:]\s*)[^\s,;]+")

def _evidence(bucket, rel, line_no, line, kind):
    safe = SECRET.sub(r"\1\2[REDACTED]", line.strip())[:220]
    bucket.append({"kind": kind, "file": rel, "line": line_no, "excerpt": safe})

def analyze_repository_deep(root: Path, inventory: dict) -> dict:
    result = {
        "analysis_type": "static_deep_scan",
        "architecture": {"top_level_directories": [], "entrypoints": [], "deployment_files": []},
        "dependencies": {"manifests": [], "package_json_dependencies": []},
        "api": {"route_candidates": []},
        "data": {"model_candidates": [], "migration_files": []},
        "security": {k: [] for k in SECURITY},
        "integrations": {k: [] for k in INTEGRATIONS},
        "configuration": {"files": [], "environment_variable_names": []},
        "tests": {"files": []},
        "symbols": {"python_classes": [], "python_functions": []},
        "parse_issues": [],
        "limitations": [
            "Análisis estático: no se ejecuta código ni se comprueba comportamiento en runtime.",
            "Las detecciones son indicios con evidencia, no afirmaciones de que una función esté activa.",
            "La reflexión, el código generado y la configuración externa pueden ocultar rutas o dependencias.",
            "No se leen valores de archivos .env; solo nombres de variables."
        ]
    }
    manifest_names = {"package.json", "pyproject.toml", "requirements.txt", "Pipfile", "pom.xml", "build.gradle", "go.mod", "Cargo.toml", "Gemfile", "composer.json", "Dockerfile", "docker-compose.yml", "compose.yaml", "openapi.yaml", "openapi.yml"}
    env_names = set()
    total_bytes = 0
    files_seen = 0
    for p in root.rglob("*"):
        rel_parts = p.relative_to(root).parts
        if any(x in SKIP for x in rel_parts) or p.is_symlink() or not p.is_file():
            continue
        files_seen += 1
        rel = p.relative_to(root).as_posix()
        if p.name in manifest_names:
            result["dependencies"]["manifests"].append(rel)
        if p.name.lower().startswith("test_") or "/tests/" in "/" + rel.lower() or rel.lower().endswith((".spec.ts", ".test.ts", ".spec.js", ".test.js")):
            result["tests"]["files"].append(rel)
        if "migration" in rel.lower() or "migrations" in rel.lower() or p.name == "schema.prisma":
            result["data"]["migration_files"].append(rel)
        if p.name in {"Dockerfile", "docker-compose.yml", "compose.yaml", "Procfile"} or "k8s" in rel.lower() or "helm" in rel.lower():
            result["architecture"]["deployment_files"].append(rel)
        if p.name in {"main.py", "app.py", "server.py", "index.js", "index.ts", "main.go", "Program.cs", "manage.py"}:
            result["architecture"]["entrypoints"].append(rel)
        if p.name.startswith(".env") or p.name in {"settings.py", "config.yaml", "config.yml"}:
            result["configuration"]["files"].append(rel)
        if p.suffix.lower() not in TEXT or p.name.startswith(".env") or p.stat().st_size > 1_000_000:
            continue
        if total_bytes + p.stat().st_size > 80_000_000:
            result["limitations"].append("Se alcanzó el límite de 80 MB de lectura; el análisis puede estar incompleto.")
            break
        try:
            source = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        total_bytes += p.stat().st_size
        if p.name == "package.json":
            try:
                pkg = json.loads(source)
                for group in ("dependencies", "devDependencies"):
                    for name, version in (pkg.get(group) or {}).items():
                        result["dependencies"]["package_json_dependencies"].append({"name": name, "version": version, "group": group, "file": rel})
            except (ValueError, AttributeError):
                result["parse_issues"].append({"file": rel, "message": "package.json inválido"})
        if p.suffix.lower() == ".py":
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        result["symbols"]["python_classes"].append({"name": node.name, "file": rel, "line": node.lineno})
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        result["symbols"]["python_functions"].append({"name": node.name, "file": rel, "line": node.lineno, "async": isinstance(node, ast.AsyncFunctionDef)})
            except SyntaxError as exc:
                result["parse_issues"].append({"file": rel, "line": exc.lineno, "message": exc.msg})
        for n, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", "*")):
                continue
            for framework, pattern in ROUTES:
                m = pattern.search(line)
                if m:
                    if framework == "FastAPI":
                        method, route = m.group(2).upper(), m.group(3)
                    elif framework == "Express":
                        method, route = m.group(2).upper(), m.group(3)
                    else:
                        method, route = "DECLARATIVE", m.group(1)
                    item = {"framework": framework, "method": method, "path": route, "file": rel, "line": n}
                    if item not in result["api"]["route_candidates"]:
                        result["api"]["route_candidates"].append(item)
            for key, pattern in SECURITY.items():
                if re.search(pattern, line):
                    _evidence(result["security"][key], rel, n, line, key)
            for key, pattern in INTEGRATIONS.items():
                if re.search(pattern, line):
                    _evidence(result["integrations"][key], rel, n, line, key)
            if re.search(r"(?i)(create_table|CREATE TABLE|schema|entity|Model\b|BaseModel)", line):
                _evidence(result["data"]["model_candidates"], rel, n, line, "data_model")
            for name in re.findall(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,})\s*=", line):
                env_names.add(name)
    result["architecture"]["top_level_directories"] = sorted(p.name for p in root.iterdir() if p.is_dir() and not p.is_symlink() and p.name not in SKIP)
    result["configuration"]["environment_variable_names"] = sorted(env_names)
    result["scan_stats"] = {
        "files_seen": files_seen, "text_bytes_read": total_bytes,
        "routes": len(result["api"]["route_candidates"]),
        "python_functions": len(result["symbols"]["python_functions"]),
        "python_classes": len(result["symbols"]["python_classes"]),
        "test_files": len(result["tests"]["files"])
    }
    for group in result["security"].values():
        del group[500:]
    for group in result["integrations"].values():
        del group[500:]
    del result["data"]["model_candidates"][1000:]
    del result["symbols"]["python_functions"][5000:]
    del result["symbols"]["python_classes"][2000:]
    return result

def build_analysis_markdown(name: str, inventory: dict, deep: dict) -> str:
    out = [
        "# Análisis técnico: " + name, "",
        "- Commit: " + str(inventory.get("commit_sha") or "desconocido"),
        "- Archivos inventariados: " + str(inventory.get("file_count_scanned", 0)),
        "- Lenguajes: " + json.dumps(inventory.get("languages", {}), ensure_ascii=False),
        "- Rutas candidatas: " + str(deep["scan_stats"]["routes"]),
        "- Funciones/clases Python: " + str(deep["scan_stats"]["python_functions"]) + "/" + str(deep["scan_stats"]["python_classes"]), "",
        "## Arquitectura", "Directorios: " + ", ".join(deep["architecture"]["top_level_directories"]),
        "Entrypoints: " + ", ".join(deep["architecture"]["entrypoints"]),
        "Despliegue: " + ", ".join(deep["architecture"]["deployment_files"]), "",
        "## Dependencias", "Manifiestos: " + ", ".join(deep["dependencies"]["manifests"]),
        "Dependencias package.json: " + str(len(deep["dependencies"]["package_json_dependencies"])), "",
        "## API"
    ]
    out.extend("- " + r["method"] + " " + r["path"] + " — " + r["file"] + ":" + str(r["line"]) for r in deep["api"]["route_candidates"])
    out += ["", "## Datos", "Candidatos de modelos: " + str(len(deep["data"]["model_candidates"])),
            "Migraciones: " + ", ".join(deep["data"]["migration_files"]), "", "## Seguridad e integraciones"]
    out.extend("- Seguridad/" + k + ": " + str(len(v)) + " indicios" for k, v in deep["security"].items())
    out.extend("- Integración/" + k + ": " + str(len(v)) + " indicios" for k, v in deep["integrations"].items())
    out += ["", "## Configuración y pruebas",
            "Variables de entorno: " + ", ".join(deep["configuration"]["environment_variable_names"]),
            "Ficheros de configuración: " + ", ".join(deep["configuration"]["files"]),
            "Ficheros de tests: " + str(len(deep["tests"]["files"])), "", "## Limitaciones"]
    out.extend("- " + x for x in deep["limitations"])
    out.append("")
    return "\n".join(out)
