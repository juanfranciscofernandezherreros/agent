import json
from datetime import datetime, timezone
import httpx
import pytest
from app.activity_analysis import analyze_activity, summarize_group
from app.agents import AnalysisContext, ActivityAnalysisAgent
from app.supervisor import default_supervisor

NOW = datetime(2026, 11, 12, tzinfo=timezone.utc)


def _client(forbid=()):
    def handler(request):
        path, q = request.url.path, dict(request.url.params)
        assert request.headers["PRIVATE-TOKEN"] == "tok"
        if any(f in path for f in forbid):
            return httpx.Response(403, json={})
        if path.endswith("/repository/branches"):
            return httpx.Response(200, json=[
                {"name": "main", "default": True, "merged": False, "commit": {"committed_date": "2026-11-10T10:00:00Z", "author_name": "Ana"}},
                {"name": "feature/x", "default": False, "merged": False, "commit": {"committed_date": "2026-10-01T10:00:00+02:00", "author_name": "Luis"}},
                {"name": "old", "default": False, "merged": True, "commit": {"committed_date": "2024-01-01T10:00:00Z", "author_name": "Ana"}}])
        if path.endswith("/repository/commits"):
            assert q["all"] == "true" and q["since"].startswith("2026-08-14")
            if q["page"] == "1":
                return httpx.Response(200, json=[{"author_name": "Ana", "committed_date": "2026-11-10T10:00:00Z"}] * 100)
            return httpx.Response(200, json=[{"author_name": "Luis", "committed_date": "2026-11-11T09:00:00Z"}] * 20)
        if path.endswith("/events"):
            assert q["action"] == "pushed"
            ev = lambda u, n, c, d="2026-11-01T00:00:00Z": {"created_at": d, "author": {"username": u, "name": n}, "push_data": {"commit_count": c}}
            return httpx.Response(200, json=[ev("ana", "Ana G", 3), ev("ana", "Ana G", 1), ev("luis", "Luis P", 10),
                                             ev("viejo", "Viejo", 1, "2026-08-13T00:00:00Z")])
        return httpx.Response(404, json={})
    return httpx.Client(transport=httpx.MockTransport(handler), headers={"PRIVATE-TOKEN": "tok"})


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "tok")
    monkeypatch.setenv("GITLAB_BASE_URL", "https://gitlab.example.com")
    monkeypatch.delenv("ACTIVITY_DAYS", raising=False)


def test_activity_counts_recent_branches_commits_and_pushes():
    a = analyze_activity(7, client=_client(), now=NOW)
    assert a["window_days"] == 90 and a["since"] == "2026-08-14"
    assert a["branches"]["total"] == 3 and a["branches"]["recent"] == 2
    assert [b["name"] for b in a["branches"]["recent_branches"]] == ["main", "feature/x"]
    assert a["commits"]["total"] == 120 and a["commits"]["by_author"] == [{"name": "Ana", "count": 100}, {"name": "Luis", "count": 20}]
    assert a["commits"]["last_commit_at"].startswith("2026-11-11")
    assert a["pushes"]["total"] == 3 and a["pushes"]["users"] == 2  # el evento fuera de ventana no cuenta
    assert a["pushes"]["top_user"] == {"user": "ana", "count": 2, "display_name": "Ana G", "commits_pushed": 4}
    assert a["errors"] == [] and "tok" not in json.dumps(a)


def test_partial_permissions_are_reported_not_fatal():
    a = analyze_activity(7, client=_client(forbid=("/events",)), now=NOW)
    assert a["pushes"]["total"] == 0 and a["errors"] == ["Pushes: sin permisos (403)"]
    assert a["commits"]["total"] == 120
    with pytest.raises(RuntimeError):
        analyze_activity(7, client=_client(forbid=("/events", "/repository")), now=NOW)


def test_group_ranking():
    def repo(name, client_now=NOW):
        return {"name": name, "agent_insights": {"activity_analysis": analyze_activity(7, client=_client(), now=NOW)}}
    quiet = {"name": "quiet", "agent_insights": {"activity_analysis": {
        "window_days": 90, "branches": {"total": 1, "recent": 0}, "commits": {"total": 0, "authors": 0, "by_author": [], "last_commit_at": None},
        "pushes": {"total": 9, "by_user": [{"user": "luis", "count": 9, "display_name": "Luis P"}], "top_user": {"user": "luis", "count": 9}}}}}
    g = summarize_group([quiet, repo("a"), repo("b"), {"name": "manual", "agent_insights": {}}])
    assert [r["repository"] for r in g["by_recent_branches"]] == ["a", "b", "quiet"]
    assert g["by_pushes"][0]["repository"] == "quiet"
    assert g["top_pusher"] == {"user": "luis", "count": 11, "display_name": "Luis P", "repositories": 3}
    assert g["top_committers"][0] == {"name": "Ana", "count": 200}
    assert g["totals"] == {"recent_branches": 4, "commits": 240, "pushes": 15}
    assert g["repositories_without_data"] == ["manual"]


def test_agent_is_skipped_for_non_gitlab_repositories(sample_repo):
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    default_supervisor().run(ctx)
    msg = ctx.store.get("activity_analysis", "svc")
    assert msg.status == "SKIPPED" and "GitLab" in msg.detail
    assert ctx.store.get("quality_analysis", "svc").status == "COMPLETED"


def test_full_flow_writes_activity_reports(sample_repo, tmp_path, monkeypatch):
    import app.analysis_orchestrator as orch
    import app.agents.activity as activity
    monkeypatch.setattr(orch, "WORKSPACES_DIR", tmp_path)
    monkeypatch.setattr(orch, "clone_repository", lambda *a, **k: sample_repo)
    monkeypatch.setattr(activity, "analyze_activity", lambda pid: analyze_activity(pid, client=_client(), now=NOW))
    result = orch.run_group_analysis("g1", "Grupo 1118", [
        {"name": "team/orders", "git_url": "https://x/a.git", "gitlab_project_id": 7},
        {"name": "team/manual", "git_url": "https://x/b.git"}])
    folder = tmp_path / "g1"
    assert result["agent_insights"]["group_activity"]["top_pusher"]["user"] == "ana"
    html = (folder / "activity.html").read_text(encoding="utf-8")
    assert "Usuarios con más pushes" in html and "Ana G" in html and "team/manual" in html
    assert "activity.html" in (folder / "index.html").read_text(encoding="utf-8")
    repo_md = (folder / "repositories" / "team-orders" / "agents.md").read_text(encoding="utf-8")
    assert "Ramas con actividad reciente" in repo_md and "feature/x" in repo_md
    saved = json.loads((folder / "repositories" / "team-orders" / "analysis.json").read_text(encoding="utf-8"))
    assert saved["agent_insights"]["activity_analysis"]["commits"]["total"] == 120
    assert "Histórico de actividad" not in (folder / "repositories" / "team-manual" / "agents.md").read_text(encoding="utf-8").split("## Agentes inteligentes")[1]


def test_gitlab_listing_keeps_project_id(monkeypatch):
    import app.gitlab as gitlab

    class FakeClient:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url, headers=None, params=None):
            return httpx.Response(200, json=[{"id": 42, "path_with_namespace": "g/s", "http_url_to_repo": "https://gitlab.example.com/g/s.git"}],
                                  request=httpx.Request("GET", url))
    monkeypatch.setattr(gitlab.httpx, "Client", FakeClient)
    assert gitlab.list_group_projects("1118") == [{"name": "g/s", "git_url": "https://gitlab.example.com/g/s.git", "gitlab_project_id": 42}]
