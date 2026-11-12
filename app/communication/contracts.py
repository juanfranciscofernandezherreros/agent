"""Contratos JSON que intercambian el supervisor y los agentes.

Todo resultado viaja dentro de un sobre ``AgentMessage`` serializable a JSON:

{
  "contract_version": "1.0", "message_id": "...", "run_id": "...",
  "agent": "quality_analysis", "scope": "repository", "repository": "team/svc",
  "status": "COMPLETED", "requires": ["deep_analysis", ...],
  "started_at": "...", "finished_at": "...", "duration_ms": 12,
  "payload": {...},            # resultado del agente (None si no terminó)
  "evidence": [Evidence, ...], # hechos trazables a archivo y línea
  "errors": [AgentError, ...],
  "detail": "motivo legible cuando el agente se omite"
}
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

CONTRACT_VERSION = "1.0"


class ContractError(ValueError):
    pass


class AgentSkipped(Exception):
    """Un agente la lanza para indicar que no procede ejecutarse (no es un error)."""


class AgentStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ALL = (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
    TERMINAL = (COMPLETED, FAILED, SKIPPED)
    TRANSITIONS = {
        PENDING: (RUNNING, SKIPPED),
        RUNNING: (COMPLETED, FAILED, SKIPPED),
        COMPLETED: (), FAILED: (), SKIPPED: (),
    }


# Niveles de confianza admitidos en una evidencia.
CONFIDENCE_LEVELS = ("observed_static", "heuristic_candidate", "inferred", "llm_inferred", "unknown")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    source_agent: str
    kind: str
    repository: str | None = None
    file: str | None = None
    line: int | None = None
    excerpt: str = ""
    confidence: str = "heuristic_candidate"
    ref: str | None = None  # identificador estable dentro del agente (p. ej. "BUG004@worker.py:2")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["excerpt"] = (self.excerpt or "")[:500]
        return data


@dataclass
class AgentError:
    agent: str
    type: str
    message: str
    recoverable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentMessage:
    agent: str
    scope: str = "repository"
    repository: str | None = None
    run_id: str | None = None
    status: str = AgentStatus.PENDING
    requires: list[str] = field(default_factory=list)
    payload: Any = None
    evidence: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    detail: str | None = None  # motivo legible (p. ej. por qué se omitió)
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    contract_version: str = CONTRACT_VERSION

    def transition(self, status: str) -> "AgentMessage":
        if status not in AgentStatus.TRANSITIONS.get(self.status, ()):
            raise ContractError(f"Transición de estado no permitida: {self.status} -> {status}")
        self.status = status
        now = utc_now()
        if status == AgentStatus.RUNNING:
            self.started_at = now
        if status in AgentStatus.TERMINAL:
            self.finished_at = now
            if self.started_at:
                delta = datetime.fromisoformat(now) - datetime.fromisoformat(self.started_at)
                self.duration_ms = int(delta.total_seconds() * 1000)
        return self

    def add_error(self, exc: BaseException | str, recoverable: bool = False) -> None:
        kind = type(exc).__name__ if isinstance(exc, BaseException) else "Error"
        self.errors.append(AgentError(self.agent, kind, str(exc)[:2000], recoverable).to_dict())

    def to_dict(self, include_payload: bool = True) -> dict:
        data = asdict(self)
        if not include_payload:
            data.pop("payload")
            data["evidence_count"] = len(data.pop("evidence"))
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMessage":
        validate_message(data)
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})


_REQUIRED = ("contract_version", "message_id", "agent", "scope", "status", "requires", "evidence", "errors")


def validate_message(data: dict) -> dict:
    """Valida que un dict cumple el contrato. Devuelve el propio dict o lanza ContractError."""
    if not isinstance(data, dict):
        raise ContractError("El mensaje debe ser un objeto JSON.")
    missing = [k for k in _REQUIRED if k not in data]
    if missing:
        raise ContractError("Faltan campos obligatorios: " + ", ".join(missing))
    if data["contract_version"] != CONTRACT_VERSION:
        raise ContractError(f"Versión de contrato no soportada: {data['contract_version']}")
    if data["status"] not in AgentStatus.ALL:
        raise ContractError(f"Estado desconocido: {data['status']}")
    if data["scope"] not in ("repository", "group"):
        raise ContractError(f"Ámbito desconocido: {data['scope']}")
    if data["scope"] == "repository" and not data.get("repository"):
        raise ContractError("Un mensaje de ámbito repository debe indicar el repositorio.")
    for name in ("requires", "evidence", "errors"):
        if not isinstance(data[name], list):
            raise ContractError(f"'{name}' debe ser una lista.")
    for item in data["evidence"]:
        if not isinstance(item, dict) or not item.get("source_agent") or not item.get("kind"):
            raise ContractError("Cada evidencia necesita 'source_agent' y 'kind'.")
        if item.get("confidence") not in CONFIDENCE_LEVELS:
            raise ContractError(f"Nivel de confianza no admitido: {item.get('confidence')}")
    for item in data["errors"]:
        if not isinstance(item, dict) or not {"agent", "type", "message"} <= set(item):
            raise ContractError("Cada error necesita 'agent', 'type' y 'message'.")
    if data["status"] == AgentStatus.FAILED and not data["errors"]:
        raise ContractError("Un mensaje FAILED debe incluir al menos un error.")
    return data
