from pathlib import Path
import subprocess
from collections import Counter
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
    if not url.startswith("https://"):
        raise ValueError("Por seguridad, esta versión solo acepta URLs Git HTTPS.")
    if any(x in url.lower() for x in ["localhost", "127.0.0.1", "169.254.", "file://"]):
        raise ValueError("La URL no está permitida.")

def clone_repository(project_id: str, git_url: str) -> Path:
    validate_git_url(git_url)
    dest = WORKSPACES_DIR / project_id / "source"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise ValueError("Ya existe un clon para este proyecto.")
    cmd = ["git", "clone", "--depth", "1", "--no-recurse-submodules", git_url, str(dest)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=MAX_CLONE_SECONDS)
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
