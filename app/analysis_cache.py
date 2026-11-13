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
import shutil
from datetime import datetime, timezone

from . import config
from .config import APP_VERSION
from .llm import status as llm_status

# Resultados que no se guardan: cambian aunque el código no cambie, o dependen de la ejecución.
NOT_CACHED = ("activity_analysis", "repository_report")


def enabled() -> bool:
    return os.getenv("ANALYSIS_CACHE", "true").strip().lower() not in {"0", "false", "no", "off"}


def _dir(item: dict):
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", item["name"]).strip("-_")[:60] or "service"
    digest = hashlib.sha1(item["git_url"].encode("utf-8")).hexdigest()[:10]
    return config.WORKSPACES_DIR / "_cache" / f"{slug}-{digest}"


def _signature(commit: str) -> dict:
    # Cambiar de proveedor o de modelo invalida la caché: las interpretaciones LLM dependen de ellos.
    info = llm_status()
    llm = (info.get("provider", "") + ":" + info.get("model", "")) if info["active"] else False
    return {"commit": commit, "app_version": APP_VERSION, "llm_agents": llm}


def load(item: dict, commit: str | None):
    """Devuelve (resultados, metadatos, carpeta de informes) si hay un análisis válido para ese commit."""
    if not enabled() or not commit:
        return None
    folder = _dir(item)
    try:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        if {k: meta.get(k) for k in ("commit", "app_version", "llm_agents")} != _signature(commit):
            return None
        results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        if not all((folder / "reports" / name).is_file() for name in meta.get("report_files", [None])):
            return None
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(results, dict) or "inventory" not in results:
        return None
    return results, meta, folder / "reports"


def save(item: dict, commit: str | None, results: dict, output_dir=None, report_files=()) -> None:
    """Guarda los resultados y una copia de los informes ya generados (sin el histórico de Git)."""
    if not enabled() or not commit:
        return
    folder = _dir(item)
    try:
        reports = folder / "reports"
        if reports.exists():
            shutil.rmtree(reports)
        reports.mkdir(parents=True, exist_ok=True)
        names = []
        for rel in report_files:
            name = str(rel).replace("\\", "/").split("/")[-1]
            shutil.copyfile(output_dir / rel, reports / name)
            names.append(name)
        data = {k: v for k, v in results.items() if k not in NOT_CACHED}
        tmp = folder / "results.json.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(folder / "results.json")
        meta = {**_signature(commit), "repository": item["name"], "report_files": names,
                "analyzed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    except OSError:
        try:
            (folder / "meta.json").unlink()  # caché incompleta: se descarta
        except OSError:
            pass
