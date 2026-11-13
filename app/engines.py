from pathlib import Path
import base64
import subprocess
from collections import Counter
from urllib.parse import urlparse
from .config import WORKSPACES_DIR, MAX_CLONE_SECONDS

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "vendor"}
EXTENSIONS = {
    ".py":"Python", ".js":"JavaScript", ".ts":"TypeScript", ".tsx":"TypeScript",
    ".jsx":"JavaScript", ".java":"Java", ".go":"Go", ".rs":"Rust", ".cs":"C#",
    ".php":"PHP", ".rb":"Ruby", ".kt":"Kotlin", ".swift":"Swift", ".sql":"SQL",
    ".yaml":"YAML", ".yml":"YAML", ".json":"JSON", ".md":"Markdown",
    ".toml":"TOML", ".xml":"XML"
}
MANIFESTS = ["package.json","pyproject.toml","requirements.txt","Pipfile","pom.xml",
             "build.gradle","go.mod","Cargo.toml","Dockerfile","docker-compose.yml",
             "compose.yaml","openapi.yaml","openapi.yml"]

def validate_git_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Por seguridad, solo se aceptan URLs Git HTTPS sin credenciales embebidas.")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.startswith("169.254."):
        raise ValueError("La URL no está permitida.")

def _git_env(git_url: str, auth_token: str | None, auth_host: str | None):
    """Entorno para Git con autenticación por cabecera; el token nunca va en la URL ni en argv."""
    parsed_host = urlparse(git_url).netloc.lower()
    if not (auth_token and auth_host and parsed_host == auth_host.lower()):
        return None
    import os
    env = os.environ.copy()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = f"http.https://{auth_host.lower()}/.extraheader"
    encoded = base64.b64encode(f"oauth2:{auth_token}".encode("utf-8")).decode("ascii")
    env["GIT_CONFIG_VALUE_0"] = f"Authorization: Basic {encoded}"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def remote_head(git_url: str, auth_token: str | None = None, auth_host: str | None = None) -> str | None:
    """Commit actual de la rama por defecto sin clonar (git ls-remote). None si no se puede saber."""
    try:
        validate_git_url(git_url)
        out = subprocess.run(["git", "ls-remote", git_url, "HEAD"], check=True, capture_output=True, text=True,
                             timeout=60, env=_git_env(git_url, auth_token, auth_host)).stdout.split()
    except (ValueError, OSError, subprocess.SubprocessError):
        return None
    return out[0] if out and len(out[0]) >= 40 else None


def local_head(path: Path) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True,
                              text=True, timeout=30).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def clone_repository(project_id: str, git_url: str, auth_token: str | None = None,
                     auth_host: str | None = None) -> Path:
    validate_git_url(git_url)
    dest = WORKSPACES_DIR / project_id / "source"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise ValueError("Ya existe un clon para este proyecto.")
    cmd = ["git", "clone", "--depth", "1", "--no-recurse-submodules", git_url, str(dest)]
    env = _git_env(git_url, auth_token, auth_host)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True,
                       timeout=MAX_CLONE_SECONDS, env=env)
    except FileNotFoundError:
        raise RuntimeError("No se encuentra Git. Instala Git for Windows.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("El clonado superó el tiempo máximo permitido.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"No se pudo clonar el repositorio: {(e.stderr or 'Error Git')[-1500:]}")
    return dest

def analyze_repository(path: Path) -> dict:
    counts, files, manifests = Counter(), [], []
    total_bytes = 0
    for p in path.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts) or not p.is_file():
            continue
        try:
            rel, size = p.relative_to(path).as_posix(), p.stat().st_size
        except OSError:
            continue
        total_bytes += size
        if p.suffix.lower() in EXTENSIONS:
            counts[EXTENSIONS[p.suffix.lower()]] += 1
        if p.name in MANIFESTS:
            manifests.append(rel)
        if len(files) < 30000:
            files.append({"path": rel, "size_bytes": size, "extension": p.suffix.lower()})
        else:
            break
    sha = None
    try:
        r = subprocess.run(["git","-C",str(path),"rev-parse","HEAD"], capture_output=True,
                           text=True, timeout=10, check=True)
        sha = r.stdout.strip()
    except Exception:
        pass
    return {
        "commit_sha": sha, "file_count_scanned": len(files), "total_size_bytes": total_bytes,
        "languages": dict(counts.most_common()), "manifests": manifests,
        "top_level": sorted(p.name for p in path.iterdir()),
        "file_inventory": files,
        "limitations": ["Análisis estático inicial; no ejecuta el código fuente.",
          "No extrae exhaustivamente reglas de negocio ni contratos dinámicos.",
          "Los resultados requieren revisión antes de reconstruir."]
    }

def build_reconstruction_package(project_name: str, analysis: dict) -> dict:
    langs = analysis.get("languages", {})
    main_lang = max(langs, key=langs.get) if langs else "Unknown"
    tasks = [
      {"id":"R-001","title":"Confirmar arquitectura y límites de componentes","status":"READY_FOR_REVIEW"},
      {"id":"R-002","title":"Documentar contratos API y catálogo de errores","status":"NEEDS_DEEP_ANALYSIS"},
      {"id":"R-003","title":"Documentar modelos de datos e invariantes","status":"NEEDS_DEEP_ANALYSIS"},
      {"id":"R-004","title":"Extraer y validar reglas de negocio","status":"NEEDS_HUMAN_REVIEW"},
      {"id":"R-005","title":"Implementar nueva versión y pruebas","status":"NOT_STARTED"},
      {"id":"R-006","title":"Ejecutar pruebas diferenciales","status":"NOT_STARTED"}]
    return {"package_version":"1.0","project_name":project_name,
      "source_commit":analysis.get("commit_sha"),"detected_primary_language":main_lang,
      "repository_inventory":analysis,"implementation_tasks":tasks,
      "reconstruction_guidance":["No asumir requisitos sin evidencia.",
        "Mantener trazabilidad requisito -> implementación -> prueba.",
        "No copiar secretos ni archivos .env.","Mantener original inmutable.",
        "Marcar UNKNOWN cualquier comportamiento no verificado."]}
