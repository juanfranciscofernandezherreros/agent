"""Provisioning and isolation primitives for autonomous Bug Hunter repositories.

The remote repository is treated as untrusted input. This module only clones GitHub
repositories; it never runs project scripts, hooks, submodules, or tests.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .config import WORKSPACES_DIR, MAX_CLONE_SECONDS

_GITHUB_HOSTS = {"github.com"}
_REPO_PATH = re.compile(r"^/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$")


@dataclass(frozen=True)
class RepositoryIdentity:
    url: str
    owner: str
    name: str
    branch: str | None = None


def validate_github_url(url: str) -> RepositoryIdentity:
    """Accept only canonical HTTPS GitHub repository URLs, without credentials."""
    if not isinstance(url, str) or not url or len(url) > 500:
        raise ValueError("URL de GitHub no válida.")
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in _GITHUB_HOSTS
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not _REPO_PATH.fullmatch(parsed.path)
    ):
        raise ValueError("Introduce una URL HTTPS de un repositorio GitHub (github.com/owner/repo).")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo or owner in {".", ".."} or repo in {".", ".."}:
        raise ValueError("Owner o nombre de repositorio no válido.")
    return RepositoryIdentity(
        url=f"https://github.com/{owner}/{repo}.git",
        owner=owner,
        name=repo,
    )


def workspace_for_agent(agent_id: str) -> Path:
    """Resolve a workspace only for a simple identifier; prevent path traversal."""
    if not isinstance(agent_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", agent_id):
        raise ValueError("Identificador de Bug Hunter no válido.")
    root = (WORKSPACES_DIR / "bug_hunters").resolve()
    path = (root / agent_id).resolve()
    if path.parent != root:
        raise ValueError("Workspace fuera del directorio permitido.")
    return path


def clone_repository(agent_id: str, github_url: str, branch: str | None = None) -> dict:
    """Clone one repository into the agent's isolated workspace without executing it."""
    identity = validate_github_url(github_url)
    if branch is not None:
        branch = branch.strip()
        if not branch or len(branch) > 250 or branch.startswith("-"):
            raise ValueError("Nombre de rama no válido.")
    workspace = workspace_for_agent(agent_id)
    source = workspace / "repository"
    if source.exists():
        raise FileExistsError("Ya existe un workspace con un clon. No se sobrescribirá.")
    workspace.mkdir(parents=True, exist_ok=True)

    cmd = ["git", "-c", "core.hooksPath=/dev/null", "clone", "--depth", "1",
           "--no-recurse-submodules", "--", identity.url, str(source)]
    if branch:
        cmd[cmd.index("clone") + 1:cmd.index("clone") + 1] = ["--branch", branch]
    try:
        subprocess.run(
            cmd, check=True, capture_output=True, text=True, timeout=MAX_CLONE_SECONDS,
            env={"PATH": __import__("os").environ.get("PATH", ""), "GIT_TERMINAL_PROMPT": "0"},
        )
        commit = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        resolved_branch = subprocess.run(
            ["git", "-C", str(source), "branch", "--show-current"],
            check=True, capture_output=True, text=True, timeout=15,
        ).stdout.strip()
    except FileNotFoundError as exc:
        raise RuntimeError("Git no está instalado o no está disponible en PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("El clonado superó el tiempo máximo permitido.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "Error de Git").strip()[-1200:]
        raise RuntimeError(f"No se pudo clonar el repositorio: {detail}") from exc

    return {
        "url": identity.url,
        "owner": identity.owner,
        "repository": identity.name,
        "workspace": str(workspace),
        "source_path": str(source),
        "branch": resolved_branch or branch,
        "commit_sha": commit,
        "status": "CLONED",
    }
