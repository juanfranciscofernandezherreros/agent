"""Histórico de actividad de un proyecto GitLab: ramas recientes, commits y pushes por usuario.

Los datos se leen de la API de GitLab (el clon es superficial y no contiene historial).
Solo lectura; el token se toma del entorno y nunca se guarda en los resultados.
"""
from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx

from .gitlab import gitlab_settings

MAX_PAGES = 50          # 5.000 elementos por consulta como máximo
TOP = 15


def activity_days() -> int:
    try:
        return max(1, min(3650, int(os.getenv("ACTIVITY_DAYS", "90"))))
    except ValueError:
        return 90


def _parse(date: str | None) -> datetime | None:
    try:
        value = datetime.fromisoformat(str(date).replace("Z", "+00:00"))
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _paged(client: httpx.Client, url: str, params: dict) -> tuple[list, bool]:
    """Devuelve (elementos, truncado). Lanza RuntimeError con un mensaje legible si GitLab rechaza la consulta."""
    items, page = [], 1
    while page <= MAX_PAGES:
        response = client.get(url, params={**params, "per_page": 100, "page": page})
        if response.status_code in (401, 403):
            raise RuntimeError(f"sin permisos ({response.status_code})")
        if response.status_code == 404:
            raise RuntimeError("no disponible (404)")
        response.raise_for_status()
        batch = response.json()
        if not isinstance(batch, list):
            raise RuntimeError("respuesta inesperada de GitLab")
        items += batch
        if len(batch) < 100:
            return items, False
        page += 1
    return items, True


def _ranking(counter: Counter, extra: dict | None = None, key: str = "name") -> list[dict]:
    return [{key: name, "count": count, **((extra or {}).get(name, {}))} for name, count in counter.most_common(TOP)]


def analyze_activity(project_id, days: int | None = None, client: httpx.Client | None = None,
                     now: datetime | None = None) -> dict:
    days = days or activity_days()
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    base_url, token, _ = gitlab_settings()
    base = f"{base_url}/api/v4/projects/{int(project_id)}"
    own = client is None
    client = client or httpx.Client(timeout=30.0, follow_redirects=False, headers={"PRIVATE-TOKEN": token})
    errors: list[str] = []
    result = {
        "source": "gitlab_api", "window_days": days, "since": since.date().isoformat(), "until": now.date().isoformat(),
        "branches": {"total": 0, "recent": 0, "recent_branches": [], "truncated": False},
        "commits": {"total": 0, "authors": 0, "by_author": [], "last_commit_at": None, "truncated": False},
        "pushes": {"total": 0, "users": 0, "by_user": [], "top_user": None, "truncated": False},
    }
    try:
        # Ramas: una rama es "reciente" si su último commit cae dentro de la ventana.
        try:
            branches, truncated = _paged(client, base + "/repository/branches", {})
            recent = []
            for b in branches:
                commit = b.get("commit") or {}
                when = _parse(commit.get("committed_date"))
                if when and when >= since:
                    recent.append({"name": b.get("name"), "last_commit_at": when.isoformat(),
                                   "last_author": commit.get("author_name"), "default": bool(b.get("default")),
                                   "merged": bool(b.get("merged"))})
            recent.sort(key=lambda x: x["last_commit_at"], reverse=True)
            result["branches"] = {"total": len(branches), "recent": len(recent), "recent_branches": recent[:TOP], "truncated": truncated}
        except (RuntimeError, httpx.HTTPError) as exc:
            errors.append(f"Ramas: {exc}")

        # Commits de todas las ramas dentro de la ventana.
        try:
            commits, truncated = _paged(client, base + "/repository/commits", {"since": since.isoformat(), "all": "true"})
            authors = Counter((c.get("author_name") or "desconocido") for c in commits)
            dates = [d for d in (_parse(c.get("committed_date")) for c in commits) if d]
            result["commits"] = {"total": len(commits), "authors": len(authors), "by_author": _ranking(authors),
                                 "last_commit_at": max(dates).isoformat() if dates else None, "truncated": truncated}
        except (RuntimeError, httpx.HTTPError) as exc:
            errors.append(f"Commits: {exc}")

        # Pushes: eventos "pushed" del proyecto (quién empuja, no quién firma el commit).
        try:
            events, truncated = _paged(client, base + "/events", {"action": "pushed", "after": (since - timedelta(days=1)).date().isoformat()})
            users, pushed_commits, names = Counter(), Counter(), {}
            for e in events:
                when = _parse(e.get("created_at"))
                if when and when < since:
                    continue
                author = e.get("author") or {}
                user = author.get("username") or e.get("author_username") or "desconocido"
                names[user] = {"display_name": author.get("name") or user}
                users[user] += 1
                pushed_commits[user] += int((e.get("push_data") or {}).get("commit_count") or 0)
            for user in names:
                names[user]["commits_pushed"] = pushed_commits[user]
            ranking = _ranking(users, names, key="user")
            result["pushes"] = {"total": sum(users.values()), "users": len(users), "by_user": ranking,
                                "top_user": ranking[0] if ranking else None, "truncated": truncated}
        except (RuntimeError, httpx.HTTPError) as exc:
            errors.append(f"Pushes: {exc}")
    finally:
        if own:
            client.close()
    if len(errors) == 3:
        raise RuntimeError("GitLab no devolvió datos de actividad. " + " | ".join(errors))
    result["errors"] = errors
    result["limitations"] = [
        f"Solo se cuenta la actividad de los últimos {days} días (configurable con ACTIVITY_DAYS).",
        "Los pushes proceden de los eventos del proyecto en GitLab; GitLab solo conserva los eventos durante un tiempo limitado.",
        "Un push puede contener muchos commits o ninguno nuevo; los commits se agrupan por el nombre de autor que figura en Git, que puede variar para una misma persona.",
        "Las consultas se limitan a 5.000 elementos; si se alcanza el límite se indica como truncado.",
    ]
    return result


def summarize_group(repositories: list[dict]) -> dict:
    """Ranking global a partir de la actividad de cada repositorio."""
    rows, pushers, committers, names = [], Counter(), Counter(), {}
    missing = []
    for repo in repositories:
        activity = (repo.get("agent_insights") or {}).get("activity_analysis")
        if not activity:
            missing.append(repo.get("name"))
            continue
        top = activity["pushes"].get("top_user") or {}
        rows.append({"repository": repo.get("name"), "recent_branches": activity["branches"]["recent"],
                     "total_branches": activity["branches"]["total"], "commits": activity["commits"]["total"],
                     "authors": activity["commits"]["authors"], "pushes": activity["pushes"]["total"],
                     "top_pusher": top.get("user"), "top_pusher_pushes": top.get("count", 0),
                     "last_commit_at": activity["commits"].get("last_commit_at")})
        for item in activity["pushes"]["by_user"]:
            pushers[item["user"]] += item["count"]
            names[item["user"]] = {"display_name": item.get("display_name") or item["user"]}
        for item in activity["commits"]["by_author"]:
            committers[item["name"]] += item["count"]
    repos_by_user = Counter()
    for repo in repositories:
        for item in ((repo.get("agent_insights") or {}).get("activity_analysis") or {}).get("pushes", {}).get("by_user", []):
            repos_by_user[item["user"]] += 1
    for user in names:
        names[user]["repositories"] = repos_by_user[user]
    window = next((a["window_days"] for a in ((r.get("agent_insights") or {}).get("activity_analysis") for r in repositories) if a), activity_days())
    by_pusher = _ranking(pushers, names, key="user")
    return {
        "window_days": window, "repositories_with_data": len(rows), "repositories_without_data": missing,
        "totals": {"recent_branches": sum(r["recent_branches"] for r in rows), "commits": sum(r["commits"] for r in rows),
                   "pushes": sum(r["pushes"] for r in rows)},
        "by_recent_branches": sorted(rows, key=lambda r: (-r["recent_branches"], r["repository"]))[:TOP * 2],
        "by_commits": sorted(rows, key=lambda r: (-r["commits"], r["repository"]))[:TOP * 2],
        "by_pushes": sorted(rows, key=lambda r: (-r["pushes"], r["repository"]))[:TOP * 2],
        "top_pushers": by_pusher, "top_pusher": by_pusher[0] if by_pusher else None,
        "top_committers": _ranking(committers),
        "limitations": ["Los rankings por usuario suman los 15 primeros de cada repositorio; la cola larga puede quedar infrarrepresentada.",
                        "Autores de commits y usuarios de push son identidades distintas (nombre en Git frente a cuenta de GitLab)."],
    }
