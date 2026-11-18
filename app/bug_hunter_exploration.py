"""Read-only exploration tools scoped to a Bug Hunter repository clone."""
from __future__ import annotations

from pathlib import Path
import re

EXCLUDED = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
MAX_READ_BYTES = 250_000
MAX_MATCHES = 500
MAX_SEARCH_FILE_BYTES = 1_000_000


def _safe_target(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    candidate = root / relative_path
    if candidate.is_symlink() or any(part.is_symlink() for part in candidate.parents if part != root):
        raise ValueError("No se permiten enlaces simbólicos.")
    target = candidate.resolve()
    if target != root and root not in target.parents:
        raise ValueError("Ruta fuera del repositorio.")
    if any(part in EXCLUDED for part in Path(relative_path).parts):
        raise ValueError("Ruta excluida de la exploración.")
    return target


def read_repository_file(root: Path, relative_path: str, max_bytes: int = MAX_READ_BYTES) -> dict:
    target = _safe_target(root, relative_path)
    if not target.is_file():
        raise FileNotFoundError(relative_path)
    size = target.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Archivo demasiado grande para lectura directa ({size} bytes).")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo no parece ser texto UTF-8.") from exc
    return {"path": Path(relative_path).as_posix(), "size_bytes": size, "content": content}


def search_repository(root: Path, query: str, *, case_sensitive: bool = False, max_matches: int = MAX_MATCHES) -> list[dict]:
    if not query or len(query) > 500:
        raise ValueError("Búsqueda vacía o demasiado larga.")
    if max_matches < 1 or max_matches > MAX_MATCHES:
        raise ValueError("Límite de resultados no válido.")
    needle = query if case_sensitive else query.casefold()
    matches = []
    for path in root.resolve().rglob("*"):
        try:
            relative = path.relative_to(root.resolve())
        except ValueError:
            continue
        if any(part in EXCLUDED for part in relative.parts) or path.is_symlink() or not path.is_file():
            continue
        try:
            if path.stat().st_size > MAX_SEARCH_FILE_BYTES:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            haystack = line if case_sensitive else line.casefold()
            if needle in haystack:
                matches.append({"path": relative.as_posix(), "line": line_number, "text": line[:1000]})
                if len(matches) >= max_matches:
                    return matches
    return matches


def find_symbol(root: Path, symbol: str, max_matches: int = MAX_MATCHES) -> list[dict]:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,199}", symbol):
        raise ValueError("Nombre de símbolo no válido.")
    pattern = re.compile(r"\b" + re.escape(symbol) + r"\b")
    matches = []
    for path in root.resolve().rglob("*"):
        try:
            relative = path.relative_to(root.resolve())
        except ValueError:
            continue
        if any(part in EXCLUDED for part in relative.parts) or path.is_symlink() or not path.is_file():
            continue
        try:
            if path.stat().st_size > MAX_SEARCH_FILE_BYTES:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            if pattern.search(line):
                matches.append({"path": relative.as_posix(), "line": line_number, "text": line[:1000]})
                if len(matches) >= max_matches:
                    return matches
    return matches
