"""Write the machine-readable security outputs (JSON + SARIF) next to the reports."""
from __future__ import annotations

import json
from pathlib import Path

from ..config import APP_VERSION
from .sarif import to_sarif


def write_security_outputs(folder, scan: dict | None) -> list[str]:
    """Always writes both files (empty results when the engine did not run) so report links stay valid."""
    folder = Path(folder)
    scan = scan or {"schema_version": "1.0", "findings": [], "summary": {"total": 0},
                    "limitations": ["El análisis de seguridad no se ejecutó en esta ejecución."]}
    (folder / "security.json").write_text(json.dumps(scan, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "security.sarif").write_text(json.dumps(to_sarif(scan, APP_VERSION), indent=2, ensure_ascii=False),
                                           encoding="utf-8")
    return ["security.json", "security.sarif"]
