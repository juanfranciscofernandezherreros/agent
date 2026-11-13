"""GitLab group discovery. Credentials are read only from process environment."""
import os
from urllib.parse import quote, urlparse

import httpx


def gitlab_settings():
    base_url = os.getenv("GITLAB_BASE_URL", "https://gitlab.com").rstrip("/")
    token = os.getenv("GITLAB_TOKEN", "").strip()
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("GITLAB_BASE_URL debe ser una URL HTTPS válida, sin credenciales.")
    if not token:
        raise RuntimeError("Falta GITLAB_TOKEN. Configura el token como variable de entorno local.")
    return base_url, token, parsed.netloc.lower()


def list_group_projects(group_id: str, allow_empty: bool = False):
    base_url, token, host = gitlab_settings()
    group = quote(str(group_id), safe="")
    headers = {"PRIVATE-TOKEN": token}
    projects, page = [], 1
    with httpx.Client(timeout=30.0, follow_redirects=False) as client:
        while True:
            response = client.get(
                f"{base_url}/api/v4/groups/{group}/projects",
                headers=headers,
                params={
                    "include_subgroups": "true",
                    "with_shared": "false",
                    "archived": "false",
                    "per_page": 100,
                    "page": page,
                    "order_by": "path",
                    "sort": "asc",
                },
            )
            if response.status_code == 401:
                raise RuntimeError("GitLab ha rechazado GITLAB_TOKEN (401).")
            if response.status_code == 403:
                raise RuntimeError("El token no tiene permisos para consultar los proyectos del grupo (403).")
            if response.status_code == 404:
                raise RuntimeError("Grupo GitLab no encontrado o no accesible con este token (404).")
            response.raise_for_status()
            batch = response.json()
            if not isinstance(batch, list):
                raise RuntimeError("Respuesta inesperada de la API de GitLab.")
            for project in batch:
                clone_url = project.get("http_url_to_repo")
                name = project.get("path_with_namespace") or project.get("name")
                if clone_url and name and urlparse(clone_url).netloc.lower() == host:
                    projects.append({"name": name, "git_url": clone_url, "gitlab_project_id": project.get("id")})
            if len(batch) < 100:
                break
            page += 1
            if page > 100:
                raise RuntimeError("El grupo supera el límite de seguridad de 10.000 proyectos.")
    if not projects and not allow_empty:
        raise RuntimeError("El grupo no contiene repositorios clonables o no hay permisos suficientes.")
    return projects


def list_accessible_groups():
    """Return groups visible to the configured GitLab token, including nested groups."""
    base_url, token, _ = gitlab_settings()
    headers = {"PRIVATE-TOKEN": token}
    groups, page = [], 1
    with httpx.Client(timeout=30.0, follow_redirects=False) as client:
        while True:
            response = client.get(f"{base_url}/api/v4/groups", headers=headers, params={
                "all_available": "true", "top_level_only": "false", "per_page": 100,
                "page": page, "order_by": "name", "sort": "asc"})
            if response.status_code == 401:
                raise RuntimeError("GitLab ha rechazado GITLAB_TOKEN (401).")
            if response.status_code == 403:
                raise RuntimeError("El token no tiene permisos para consultar los grupos (403).")
            response.raise_for_status()
            batch = response.json()
            if not isinstance(batch, list):
                raise RuntimeError("Respuesta inesperada de la API de grupos de GitLab.")
            for group in batch:
                if group.get("id") is not None:
                    groups.append({"id": group["id"], "name": group.get("name") or str(group["id"]),
                        "full_path": group.get("full_path") or str(group["id"]),
                        "parent_id": group.get("parent_id"), "web_url": group.get("web_url")})
            if len(batch) < 100:
                break
            page += 1
            if page > 100:
                raise RuntimeError("La cuenta supera el límite de seguridad de 10.000 grupos.")
    return groups