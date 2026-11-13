"""Caché de análisis por repositorio.

Si un repositorio no ha cambiado (mismo commit en su rama por defecto) y la versión de la
herramienta es la misma, se reutilizan sus resultados y no se vuelve a clonar ni analizar.
Se desactiva con ANALYSIS_CACHE=false.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone

from . import config
from .config import APP_VERSION
from .llm import agents_enabled

# Resultados que no se guardan: cambian aunque el código no cambie, o dependen de la ejecución.
NOT_CACHED = ("activity_analysis", "repository_report")


def enabled() -> bool:
    return os.getenv("ANALYSIS_CACHE", "true").strip().lower() not in {"0", "false", "no", "off"}


def _dir(item: dict):
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", item["name"]).strip("-_")[:60] or "service"
    digest = hashlib.sha1(item["git_url"].encode("utf-8")).hexdigest()[:10]
    return config.WORKSPACES_DIR / "_cache" / f"{slug}-{digest}"


def _signature(commit: str) -> dict:
    return {"commit": commit, "app_version": APP_VERSION, "llm_agents": agents_enabled()}


def load(item: dict, commit: str | None) -> tuple[dict, dict] | None:
    """Devuelve (resultados, metadatos) si hay un análisis válido para ese commit."""
    if not enabled() or not commit:
        return None
    folder = _dir(item)
    try:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        if {k: meta.get(k) for k in ("commit", "app_version", "llm_agents")} != _signature(commit):
            return None
        results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return (results, meta) if isinstance(results, dict) and "inventory" in results else None


def save(item: dict, commit: str | None, results: dict) -> None:
    if not enabled() or not commit:
        return
    folder = _dir(item)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        data = {k: v for k, v in results.items() if k not in NOT_CACHED}
        tmp = folder / "results.json.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(folder / "results.json")
        meta = {**_signature(commit), "repository": item["name"],
                "analyzed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # la caché es una optimización: si no se puede escribir, el análisis sigue
