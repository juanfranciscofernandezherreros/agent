"""Almacén compartido (pizarra) donde los agentes publican y leen mensajes.

Vive en memoria y, si se le da una carpeta, persiste cada mensaje como JSON:

    <carpeta>/manifest.json
    <carpeta>/<repositorio|_group>/<agente>.json
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from .contracts import AgentMessage, AgentStatus, CONTRACT_VERSION, validate_message

GROUP_KEY = "_group"


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-_")[:60] or "service"


class SharedStore:
    def __init__(self, directory: Path | None = None, run_id: str | None = None):
        self.directory = Path(directory) if directory else None
        self.run_id = run_id
        self._messages: dict[tuple[str, str], AgentMessage] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(agent: str, repository: str | None) -> tuple[str, str]:
        return (repository or GROUP_KEY, agent)

    def publish(self, message: AgentMessage) -> AgentMessage:
        if message.run_id is None:
            message.run_id = self.run_id
        data = validate_message(message.to_dict())
        with self._lock:
            self._messages[self._key(message.agent, message.repository)] = message
            if self.directory and message.status in AgentStatus.TERMINAL:
                folder = self.directory / (_slug(message.repository) if message.repository else GROUP_KEY)
                folder.mkdir(parents=True, exist_ok=True)
                (folder / (message.agent + ".json")).write_text(
                    json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
                self._write_manifest()
        return message

    def get(self, agent: str, repository: str | None = None) -> AgentMessage | None:
        return self._messages.get(self._key(agent, repository))

    def payload(self, agent: str, repository: str | None = None):
        message = self.get(agent, repository)
        return message.payload if message and message.status == AgentStatus.COMPLETED else None

    def messages(self, repository: str | None = None, scope: str | None = None) -> list[AgentMessage]:
        out = list(self._messages.values())
        if repository is not None:
            out = [m for m in out if m.repository == repository]
        if scope is not None:
            out = [m for m in out if m.scope == scope]
        return out

    def evidence(self, repository: str | None = None, agent: str | None = None) -> list[dict]:
        return [e for m in self.messages(repository) if agent in (None, m.agent) for e in m.evidence]

    def errors(self, repository: str | None = None) -> list[dict]:
        return [e for m in self.messages(repository) for e in m.errors]

    def manifest(self) -> dict:
        """Resumen sin payloads: estado de cada agente por repositorio."""
        repos: dict[str, list[dict]] = {}
        for (repo, _), message in self._messages.items():
            repos.setdefault(repo, []).append(message.to_dict(include_payload=False))
        counts: dict[str, int] = {}
        for message in self._messages.values():
            counts[message.status] = counts.get(message.status, 0) + 1
        return {"contract_version": CONTRACT_VERSION, "run_id": self.run_id,
                "status_counts": counts, "group": repos.pop(GROUP_KEY, []), "repositories": repos}

    def _write_manifest(self) -> None:
        (self.directory / "manifest.json").write_text(
            json.dumps(self.manifest(), indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    @classmethod
    def load(cls, directory: Path) -> "SharedStore":
        """Reconstruye el almacén desde disco (para otros procesos o ejecuciones posteriores)."""
        store = cls(directory)
        for path in sorted(Path(directory).glob("*/*.json")):
            message = AgentMessage.from_dict(json.loads(path.read_text(encoding="utf-8")))
            store.run_id = store.run_id or message.run_id
            store._messages[cls._key(message.agent, message.repository)] = message
        return store
