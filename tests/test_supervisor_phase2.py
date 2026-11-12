import json
import pytest
from app.agents import AnalysisContext
from app.agents.context import AnalyzerAgent
from app.supervisor import Supervisor, SupervisorError, default_supervisor


def _agent(name, requires=(), scope="repository", log=None):
    class A(AnalyzerAgent):
        def run(self, context):
            if log is not None:
                log.append(name)
            context.results[name] = {"ok": name}
            return context.results[name]
    a = A(); a.name = name; a.requires = tuple(requires); a.scope = scope
    return a


def test_default_plan_respects_dependencies():
    sup = default_supervisor()
    order = [a.name for a in sup.plan("repository")]
    assert order == ["inventory", "deep_analysis", "functional_analysis", "java_analysis", "quality_analysis"]
    assert [a.name for a in sup.plan("group")] == ["integration_analysis"]
    assert sup.describe_plan()[1] == {"step": 2, "agent": "deep_analysis", "scope": "repository", "requires": ["inventory"]}


def test_plan_reorders_agents_registered_out_of_order():
    log = []
    sup = Supervisor([_agent("c", ["b"], log=log), _agent("b", ["a"], log=log), _agent("a", log=log)])
    sup.run(AnalysisContext())
    assert log == ["a", "b", "c"]


def test_only_selects_targets_and_their_dependencies():
    sup = default_supervisor()
    assert [a.name for a in sup.plan(only=["deep_analysis"])] == ["inventory", "deep_analysis"]
    with pytest.raises(SupervisorError):
        sup.plan(only=["nope"])


def test_invalid_graphs_are_rejected():
    with pytest.raises(SupervisorError):
        Supervisor([_agent("a", ["b"]), _agent("b", ["a"])])
    with pytest.raises(SupervisorError):
        Supervisor([_agent("a", ["missing"])])
    with pytest.raises(SupervisorError):
        Supervisor([_agent("a"), _agent("a")])


def test_supervisor_does_not_recompute_available_results():
    log = []
    sup = Supervisor([_agent("a", log=log), _agent("b", ["a"], log=log)])
    sup.run(AnalysisContext(results={"a": {"cached": True}}))
    assert log == ["b"]


def test_group_analysis_end_to_end(sample_repo, tmp_path, monkeypatch):
    """El flujo completo produce los mismos artefactos pasando por el supervisor."""
    import app.analysis_orchestrator as orch
    monkeypatch.setattr(orch, "WORKSPACES_DIR", tmp_path / "ws")
    monkeypatch.setattr(orch, "clone_repository", lambda *a, **k: sample_repo)
    result = orch.run_group_analysis("g1", "Grupo", [{"name": "team/svc", "git_url": "https://x/y.git"}])
    folder = tmp_path / "ws" / "g1"
    assert result["completion_status"] == "STATIC_ANALYSIS_COMPLETED"
    repo = result["repositories"][0]
    assert repo["java_analysis"]["summary"]["classes"] >= 2
    topics = {t["topic"] for t in result["integration_analysis"]["topic_candidates"]}
    assert "orders.created" in topics
    for rel in ("analysis.json", "analysis.md", "analysis.html", "index.html", "bug-reports/index.html",
                "repositories/team-svc/analysis.json", "repositories/team-svc/analysis.html"):
        assert (folder / rel).is_file(), rel
    json.loads((folder / "analysis.json").read_text(encoding="utf-8"))
