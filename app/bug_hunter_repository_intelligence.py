"""Static repository mapping for Bug Hunter. Never executes repository code."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess

EXCLUDED = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".java": "Java", ".go": "Go", ".rs": "Rust", ".cs": "C#",
    ".php": "PHP", ".rb": "Ruby", ".kt": "Kotlin", ".swift": "Swift", ".sql": "SQL",
}
TEST_MARKERS = ("test_", "_test.", ".spec.", ".test.")
ENTRYPOINT_NAMES = {"main.py", "main.js", "main.ts", "index.js", "index.ts", "app.py", "app.js", "manage.py"}
MANIFEST_NAMES = {"pyproject.toml", "requirements.txt", "package.json", "pom.xml", "build.gradle", "go.mod", "Cargo.toml", "Dockerfile", "docker-compose.yml", "compose.yaml"}
MAX_FILES = 50000
MAX_FILE_BYTES = 2_000_000


def scan_repository(root: Path) -> dict:
    root = root.resolve()
    counts = Counter()
    inventory = []
    tests = []
    entrypoints = []
    manifests = []
    total_bytes = 0
    truncated = False

    for path in root.rglob("*"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if len(inventory) >= MAX_FILES:
            truncated = True
            break
        try:
            size = path.stat().st_size
        except OSError:
            continue
        rel = relative.as_posix()
        ext = path.suffix.lower()
        if ext in LANGUAGES:
            counts[LANGUAGES[ext]] += 1
        total_bytes += size
        inventory.append({"path": rel, "size_bytes": size, "language": LANGUAGES.get(ext)})
        if any(marker in path.name.lower() for marker in TEST_MARKERS) or "tests" in relative.parts or "test" in relative.parts:
            tests.append(rel)
        if path.name.lower() in ENTRYPOINT_NAMES:
            entrypoints.append(rel)
        if path.name in MANIFEST_NAMES:
            manifests.append(rel)

    commit = None
    branch = None
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, timeout=15).stdout.strip()
        branch = subprocess.run(["git", "-C", str(root), "branch", "--show-current"], check=True, capture_output=True, text=True, timeout=15).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass

    return {
        "schema_version": "1.0",
        "commit_sha": commit,
        "branch": branch,
        "file_count": len(inventory),
        "total_size_bytes": total_bytes,
        "languages": dict(counts.most_common()),
        "entrypoints": sorted(entrypoints)[:500],
        "test_files": sorted(tests)[:2000],
        "manifests": sorted(manifests)[:500],
        "file_inventory": inventory,
        "truncated": truncated,
        "limits": {"max_files": MAX_FILES, "max_file_bytes_for_future_read": MAX_FILE_BYTES},
        "execution_policy": "SOURCE_NOT_EXECUTED",
    }
