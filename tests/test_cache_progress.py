import json
import pytest
import app.analysis_orchestrator as orch
from app import analysis_cache, config

REPOS = [{"name": "team/orders", "git_url": "https://x/a.git"}, {"name": "team/billing", "git_url": "https://x/b.git"}]


@pytest.fixture
def env(sample_repo, tmp_path, monkeypatch):
    state = {"clones": [], "heads": {"https://x/a.git": "a" * 40, "https://x/b.git": "b" * 40}}
    monkeypatch.setattr(orch, "WORKSPACES_DIR", tmp_path)
    monkeypatch.setattr(config, "WORKSPACES_DIR", tmp_path)
    monkeypatch.setattr(orch, "clone_repository", lambda mid, url, **k: state["clones"].append(url) or sample_repo)
    monkeypatch.setattr(orch.engines, "remote_head", lambda url, *a: state["heads"].get(url))
    monkeypatch.setattr(orch.engines, "local_head", lambda path: None)
    state["tmp"] = tmp_path
    return state


def _strip(result):
    data = json.loads(json.dumps(result))
    data.pop("agent_runs")
    return data


def test_second_run_reuses_unchanged_repositories(env):
    first = orch.run_group_analysis("g1", "Grupo", REPOS)
    assert len(env["clones"]) == 2
    second = orch.run_group_analysis("g2", "Grupo", REPOS)
    assert len(env["clones"]) == 2  # nada se vuelve a clonar
    assert _strip(first) == _strip(second)  # mismo resultado
    folder = env["tmp"] / "g2"
    for rel in ("index.html", "analysis.html", "repositories/team-orders/analysis.html",
                "repositories/team-billing/agents.html", "bug-reports/002-team-billing.html"):
        assert (folder / rel).is_file(), rel
    assert "Análisis reutilizado" in (folder / "repositories" / "team-orders" / "agents.md").read_text(encoding="utf-8")
    progress = json.loads((folder / "progress.json").read_text(encoding="utf-8"))
    assert progress["reused"] == 2 and [i["status"] for i in progress["items"]] == ["reused", "reused"]


def test_changed_repository_is_reanalysed(env):
    orch.run_group_analysis("g1", "Grupo", REPOS)
    env["heads"]["https://x/b.git"] = "c" * 40
    orch.run_group_analysis("g2", "Grupo", REPOS)
    assert env["clones"] == ["https://x/a.git", "https://x/b.git", "https://x/b.git"]
    progress = json.loads((env["tmp"] / "g2" / "progress.json").read_text(encoding="utf-8"))
    assert [i["status"] for i in progress["items"]] == ["reused", "done"]


def test_interrupted_run_resumes_from_what_was_done(env, monkeypatch):
    original = orch.clone_repository

    def flaky(mid, url, **k):
        if url.endswith("b.git"):
            raise RuntimeError("corte de red")
        return original(mid, url, **k)
    monkeypatch.setattr(orch, "clone_repository", flaky)
    partial = orch.run_group_analysis("g1", "Grupo", REPOS)
    assert partial["completion_status"] == "PARTIAL_ANALYSIS_COMPLETED"
    monkeypatch.setattr(orch, "clone_repository", original)
    env["clones"].clear()
    done = orch.run_group_analysis("g2", "Grupo", REPOS)
    assert env["clones"] == ["https://x/b.git"] and done["completion_status"] == "STATIC_ANALYSIS_COMPLETED"


def test_cache_is_ignored_when_disabled_version_changes_or_head_unknown(env, monkeypatch):
    orch.run_group_analysis("g1", "Grupo", REPOS[:1])
    monkeypatch.setenv("ANALYSIS_CACHE", "false")
    orch.run_group_analysis("g2", "Grupo", REPOS[:1])
    assert len(env["clones"]) == 2
    monkeypatch.delenv("ANALYSIS_CACHE")
    monkeypatch.setattr(analysis_cache, "APP_VERSION", "99.0")
    orch.run_group_analysis("g3", "Grupo", REPOS[:1])
    assert len(env["clones"]) == 3
    env["heads"].clear()  # ls-remote falla: no se puede saber si cambió
    orch.run_group_analysis("g4", "Grupo", REPOS[:1])
    assert len(env["clones"]) == 4


def test_progress_is_written_after_each_repository(env, monkeypatch):
    seen = []
    original = orch._write_progress
    monkeypatch.setattr(orch, "_write_progress", lambda folder, s: (seen.append((s["phase"], s["completed"], s["current"])), original(folder, s))[1])
    orch.run_group_analysis("g1", "Grupo", REPOS)
    assert seen == [("repositories", 0, "team/orders"), ("repositories", 1, "team/orders"),
                    ("repositories", 1, "team/billing"), ("repositories", 2, "team/billing"),
                    ("global", 2, None), ("done", 2, None)]
    # el HTML del primer repositorio ya existe antes de empezar el segundo
    item = json.loads((env["tmp"] / "g1" / "progress.json").read_text(encoding="utf-8"))["items"][0]
    assert item == {"name": "team/orders", "status": "done", "artifact_dir": "repositories/team-orders",
                    "bug_report": "bug-reports/001-team-orders.html"}


def test_progress_endpoint(env, monkeypatch, tmp_path):
    import app.main as main
    monkeypatch.setattr(main, "WORKSPACES_DIR", env["tmp"])

    class Con:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, *a):
            class R:
                def fetchone(self_inner): return {"status": "ANALYZING", "last_error": None}
            return R()
    monkeypatch.setattr(main, "connect", lambda: Con())
    assert main.get_analysis_group_progress("nuevo") == {"status": "ANALYZING", "last_error": None, "progress": None}
    orch.run_group_analysis("g1", "Grupo", REPOS[:1])
    assert main.get_analysis_group_progress("g1")["progress"]["completed"] == 1


def test_remote_head_uses_ls_remote(monkeypatch):
    from app import engines
    calls = []

    class Done:
        stdout = "d" * 40 + "\tHEAD\n"
    monkeypatch.setattr(engines.subprocess, "run", lambda cmd, **k: calls.append((cmd, k.get("env"))) or Done())
    assert engines.remote_head("https://gitlab.example.com/g/s.git", "secret", "gitlab.example.com") == "d" * 40
    cmd, env_ = calls[0]
    assert cmd == ["git", "ls-remote", "https://gitlab.example.com/g/s.git", "HEAD"] and "secret" not in " ".join(cmd)
    assert env_["GIT_CONFIG_KEY_0"] == "http.https://gitlab.example.com/.extraheader"
    assert engines.remote_head("http://inseguro/x.git") is None
