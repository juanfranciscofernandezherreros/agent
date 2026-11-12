"""Adapter-neutral differential comparison for exported state and side-effect snapshots.

Expected shape:
{
  "database": {"schema": {...}, "tables": {"users": [{"id": 1, ...}]}},
  "events": [{"name": "...", "payload": {...}}],
  "integrations": [{"provider": "...", "operation": "...", "request": {...}, "response": {...}}]
}
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

CATEGORIES = ("database", "events", "integrations")


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    return value


def _fingerprint(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _database_differences(left: Any, right: Any) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    left = left or {}
    right = right or {}
    if _canonical(left.get("schema", {})) != _canonical(right.get("schema", {})):
        differences.append({"path": "database.schema", "kind": "SCHEMA_MISMATCH",
                           "original": left.get("schema", {}), "reconstructed": right.get("schema", {})})
    lt, rt = left.get("tables", {}), right.get("tables", {})
    for table in sorted(set(lt) | set(rt)):
        lrows, rrows = lt.get(table, []), rt.get(table, [])
        lc, rc = Counter(map(_fingerprint, lrows)), Counter(map(_fingerprint, rrows))
        if lc == rc:
            continue
        lset, rset = set(lc), set(rc)
        for item in sorted(lset - rset):
            differences.append({"path": f"database.tables.{table}", "kind": "ROW_MISSING_IN_RECONSTRUCTED",
                                "row": json.loads(item), "count": lc[item] - rc[item]})
        for item in sorted(rset - lset):
            differences.append({"path": f"database.tables.{table}", "kind": "UNEXPECTED_ROW_IN_RECONSTRUCTED",
                                "row": json.loads(item), "count": rc[item] - lc[item]})
        for item in sorted(lset & rset):
            if lc[item] != rc[item]:
                differences.append({"path": f"database.tables.{table}", "kind": "ROW_COUNT_MISMATCH",
                                    "row": json.loads(item), "original_count": lc[item],
                                    "reconstructed_count": rc[item]})
    return differences


def _sequence_differences(category: str, left: Any, right: Any) -> list[dict[str, Any]]:
    left, right = left or [], right or []
    differences: list[dict[str, Any]] = []
    if len(left) != len(right):
        differences.append({"path": category, "kind": "COUNT_MISMATCH",
                            "original_count": len(left), "reconstructed_count": len(right)})
    for index in range(max(len(left), len(right))):
        a = left[index] if index < len(left) else None
        b = right[index] if index < len(right) else None
        if _canonical(a) != _canonical(b):
            differences.append({"path": f"{category}[{index}]", "kind": "ITEM_MISMATCH",
                                "original": a, "reconstructed": b})
    return differences


def compare_state_snapshots(original: dict[str, Any], reconstructed: dict[str, Any]) -> dict[str, Any]:
    """Compare database contents/schema, emitted events and integration call traces."""
    differences: dict[str, list[dict[str, Any]]] = {
        "database": _database_differences(original.get("database"), reconstructed.get("database")),
        "events": _sequence_differences("events", original.get("events"), reconstructed.get("events")),
        "integrations": _sequence_differences("integrations", original.get("integrations"),
                                              reconstructed.get("integrations")),
    }
    statuses = {name: ("VERIFIED" if not items else "MISMATCH") for name, items in differences.items()}
    total = sum(len(items) for items in differences.values())
    return {
        "summary": {"dimensions": len(CATEGORIES), "verified": sum(v == "VERIFIED" for v in statuses.values()),
                    "mismatched": sum(v == "MISMATCH" for v in statuses.values()),
                    "difference_count": total},
        "dimension_status": statuses,
        "overall_status": "MATCH" if total == 0 else "MISMATCH",
        "differences": differences,
        "limitations": [
            "Compara snapshots exportados; no se conecta por sí solo a motores SQL, brokers o APIs externas.",
            "Los snapshots deben capturarse para el mismo escenario y en entornos equivalentes.",
            "Las secuencias de eventos e integraciones se comparan en orden; solo se normaliza el orden de filas DB.",
            "No se ignoran automáticamente timestamps, UUID ni otros valores no deterministas: deben normalizarse explícitamente antes de enviar el snapshot.",
            "MATCH significa coincidencia de estos snapshots, no equivalencia universal del servicio."
        ]
    }
