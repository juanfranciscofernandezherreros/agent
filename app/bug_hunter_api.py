"""API routes for creating and monitoring isolated Bug Hunter clones."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from .database import connect
from .bug_hunter_provisioning import clone_repository, validate_github_url
from .bug_hunter_repository_intelligence import scan_repository
from .bug_hunter_exploration import read_repository_file, search_repository, find_symbol

router = APIRouter(prefix="/api/bug-hunters", tags=["Bug Hunter"])


class BugHunterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    github_url: str = Field(min_length=8, max_length=500)
    branch: str | None = Field(default=None, max_length=250)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clone_task(agent_id: str, url: str, branch: str | None) -> None:
    with connect() as con:
        con.execute("UPDATE bug_hunters SET status='CLONING',updated_at=?,last_error=NULL WHERE id=?",
                    (now(), agent_id))
    try:
        result = clone_repository(agent_id, url, branch)
        with connect() as con:
            con.execute("UPDATE bug_hunters SET status='MAPPING_REPOSITORY',updated_at=? WHERE id=?", (now(), agent_id))
        repository_map = scan_repository(Path(result['source_path']))
        result['repository_map'] = repository_map
        with connect() as con:
            con.execute("UPDATE bug_hunters SET status='READY_FOR_HUNT',repository_json=?,updated_at=? WHERE id=?",
                        (json.dumps(result, ensure_ascii=False), now(), agent_id))
    except Exception as exc:
        with connect() as con:
            con.execute("UPDATE bug_hunters SET status='INITIALIZATION_FAILED',last_error=?,updated_at=? WHERE id=?",
                        (str(exc)[:2000], now(), agent_id))


@router.post("", status_code=202)
def create_bug_hunter(payload: BugHunterCreate, background_tasks: BackgroundTasks):
    try:
        identity = validate_github_url(payload.github_url)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    agent_id = str(uuid.uuid4())
    timestamp = now()
    with connect() as con:
        con.execute(
            "INSERT INTO bug_hunters(id,name,github_url,branch,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            (agent_id, payload.name.strip(), identity.url, payload.branch, "QUEUED", timestamp, timestamp),
        )
    background_tasks.add_task(_clone_task, agent_id, identity.url, payload.branch)
    return {"bug_hunter_id": agent_id, "status": "QUEUED", "message": "Clonado de GitHub iniciado."}


@router.get("")
def list_bug_hunters():
    with connect() as con:
        rows = con.execute(
            "SELECT id,name,github_url,branch,status,created_at,updated_at,last_error FROM bug_hunters ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/{agent_id}")
def get_bug_hunter(agent_id: str):
    with connect() as con:
        row = con.execute("SELECT * FROM bug_hunters WHERE id=?", (agent_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Bug Hunter no encontrado.")
    result = dict(row)
    if result.get("repository_json"):
        result["repository"] = json.loads(result.pop("repository_json"))
    return result


@router.get("/{agent_id}/repository-map")
def get_repository_map(agent_id: str):
    hunter = get_bug_hunter(agent_id)
    repository = hunter.get("repository") or {}
    mapping = repository.get("repository_map")
    if not mapping:
        raise HTTPException(409, "El mapa del repositorio todavía no está disponible.")
    return mapping



def _repository_root(agent_id: str) -> Path:
    hunter = get_bug_hunter(agent_id)
    repository = hunter.get("repository") or {}
    source_path = repository.get("source_path")
    if not source_path:
        raise HTTPException(409, "El repositorio todavía no está clonado.")
    source = Path(source_path).resolve()
    expected = Path(repository.get("workspace", "")).resolve() / "repository"
    if source != expected or not source.is_dir():
        raise HTTPException(409, "El workspace del repositorio no es válido.")
    return source


@router.get("/{agent_id}/file")
def read_hunter_file(agent_id: str, path: str):
    root = _repository_root(agent_id)
    try:
        return read_repository_file(root, path)
    except FileNotFoundError:
        raise HTTPException(404, "Archivo no encontrado.")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.get("/{agent_id}/search")
def search_hunter_repository(agent_id: str, q: str, case_sensitive: bool = False):
    root = _repository_root(agent_id)
    try:
        return {"matches": search_repository(root, q, case_sensitive=case_sensitive)}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.get("/{agent_id}/symbols/{symbol}")
def find_hunter_symbol(agent_id: str, symbol: str):
    root = _repository_root(agent_id)
    try:
        return {"matches": find_symbol(root, symbol)}
    except ValueError as exc:
        raise HTTPException(400, str(exc))

class InvestigationCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    hypothesis: str = Field(min_length=10, max_length=5000)
    scope: list[str] = Field(default_factory=list, max_length=100)


@router.post("/{agent_id}/investigations", status_code=202)
def create_investigation(agent_id: str, payload: InvestigationCreate):
    _repository_root(agent_id)
    investigation_id = str(uuid.uuid4())
    timestamp = now()
    with connect() as con:
        con.execute(
            """INSERT INTO bug_hunter_investigations
            (id,agent_id,title,hypothesis,scope_json,status,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (investigation_id, agent_id, payload.title.strip(), payload.hypothesis.strip(),
             json.dumps(payload.scope, ensure_ascii=False), "QUEUED", timestamp, timestamp),
        )
    return {"investigation_id": investigation_id, "status": "QUEUED"}


@router.get("/{agent_id}/investigations")
def list_investigations(agent_id: str):
    get_bug_hunter(agent_id)
    with connect() as con:
        rows = con.execute(
            """SELECT id,title,status,created_at,updated_at,last_error
            FROM bug_hunter_investigations WHERE agent_id=? ORDER BY created_at DESC""",
            (agent_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/{agent_id}/investigations/{investigation_id}")
def get_investigation(agent_id: str, investigation_id: str):
    get_bug_hunter(agent_id)
    with connect() as con:
        row = con.execute(
            "SELECT * FROM bug_hunter_investigations WHERE id=? AND agent_id=?",
            (investigation_id, agent_id),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Investigación no encontrada.")
    result = dict(row)
    result["scope"] = json.loads(result.pop("scope_json"))
    result["evidence"] = json.loads(result.pop("evidence_json") or "[]")
    return result

class EvidenceCreate(BaseModel):
    kind: str = Field(min_length=2, max_length=40)
    summary: str = Field(min_length=3, max_length=2000)
    file: str | None = Field(default=None, max_length=500)
    line: int | None = Field(default=None, ge=1)
    detail: str | None = Field(default=None, max_length=10000)


class InvestigationStatusUpdate(BaseModel):
    status: str
    last_error: str | None = Field(default=None, max_length=2000)


_ALLOWED_INVESTIGATION_STATUSES = {
    "QUEUED", "PLANNING", "EXPLORING", "VALIDATING",
    "CONFIRMED", "PROBABLE", "UNCONFIRMED", "DISCARDED", "BLOCKED",
}


@router.post("/{agent_id}/investigations/{investigation_id}/evidence", status_code=201)
def append_investigation_evidence(agent_id: str, investigation_id: str, payload: EvidenceCreate):
    get_bug_hunter(agent_id)
    record = payload.model_dump()
    record["recorded_at"] = now()
    with connect() as con:
        row = con.execute(
            "SELECT evidence_json,status FROM bug_hunter_investigations WHERE id=? AND agent_id=?",
            (investigation_id, agent_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Investigación no encontrada.")
        if row["status"] in {"CONFIRMED", "PROBABLE", "UNCONFIRMED", "DISCARDED"}:
            raise HTTPException(409, "La investigación ya está cerrada.")
        evidence = json.loads(row["evidence_json"] or "[]")
        if len(evidence) >= 1000:
            raise HTTPException(409, "La investigación alcanzó el límite de evidencias.")
        evidence.append(record)
        con.execute(
            "UPDATE bug_hunter_investigations SET evidence_json=?,updated_at=? WHERE id=?",
            (json.dumps(evidence, ensure_ascii=False), now(), investigation_id),
        )
    return {"investigation_id": investigation_id, "evidence_count": len(evidence), "recorded": True}


@router.post("/{agent_id}/investigations/{investigation_id}/status")
def update_investigation_status(agent_id: str, investigation_id: str, payload: InvestigationStatusUpdate):
    get_bug_hunter(agent_id)
    new_status = payload.status.strip().upper()
    if new_status not in _ALLOWED_INVESTIGATION_STATUSES:
        raise HTTPException(400, "Estado de investigación no válido.")
    with connect() as con:
        row = con.execute(
            "SELECT status FROM bug_hunter_investigations WHERE id=? AND agent_id=?",
            (investigation_id, agent_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Investigación no encontrada.")
        old_status = row["status"]
        if old_status in {"CONFIRMED", "PROBABLE", "UNCONFIRMED", "DISCARDED"}:
            raise HTTPException(409, "La investigación está cerrada.")
        if new_status == "CONFIRMED":
            count = con.execute(
                "SELECT COUNT(*) FROM bug_hunter_investigations WHERE agent_id=? AND status='CONFIRMED'",
                (agent_id,),
            ).fetchone()[0]
            # Confirmation is a state label, not proof: evidence remains mandatory.
            evidence = con.execute(
                "SELECT evidence_json FROM bug_hunter_investigations WHERE id=?",
                (investigation_id,),
            ).fetchone()[0]
            if not evidence or len(json.loads(evidence)) < 2:
                raise HTTPException(409, "Para confirmar se requieren al menos dos evidencias registradas.")
        con.execute(
            "UPDATE bug_hunter_investigations SET status=?,last_error=?,updated_at=? WHERE id=?",
            (new_status, payload.last_error, now(), investigation_id),
        )
    return {"investigation_id": investigation_id, "previous_status": old_status, "status": new_status}
