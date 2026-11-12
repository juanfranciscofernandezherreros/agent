import json
import pytest
from app.agents import AnalysisContext
from app.agents.context import AnalyzerAgent
from app.communication import (
    AgentMessage, AgentSkipped, AgentStatus, ContractError, Evidence, SharedStore, validate_message,
)
from app.supervisor import Supervisor, default_supervisor


def _agent(name, requires=(), optional=False, behaviour=None):
    class A(AnalyzerAgent):
        def run(self, context):
            if behaviour:
                behaviour()
            return {"ok": name}
    a = A(); a.name = name; a.requires = tuple(requires); a.optional = optional
    return a


def _raise(exc):
    def f():
        raise exc
    return f


def test_message_contract_roundtrip_and_validation():
    msg = AgentMessage(agent="x", repository="svc")
    msg.transition(AgentStatus.RUNNING).transition(AgentStatus.COMPLETED)
    msg.evidence.append(Evidence(source_agent="x", kind="k", file="a.py", line=1).to_dict())
    data = json.loads(json.dumps(msg.to_dict()))
    assert AgentMessage.from_dict(data).to_dict() == data
    assert data["duration_ms"] is not None and data["contract_version"] == "1.0"
    with pytest.raises(ContractError):
        msg.transition(AgentStatus.RUNNING)  # los estados terminales no cambian
    for broken in ({**data, "status": "DONE"}, {**data, "repository": None},
                   {**data, "status": "FAILED", "errors": []},
                   {**data, "evidence": [{"kind": "k"}]},
                   {k: v for k, v in data.items() if k != "agent"}):
        with pytest.raises(ContractError):
            validate_message(broken)


def test_store_persists_and_reloads(tmp_path):
    store = SharedStore(tmp_path / "runs", run_id="r1")
    msg = AgentMessage(agent="a", repository="team/svc")
    store.publish(msg)
    msg.payload = {"n": 1}
    store.publish(msg.transition(AgentStatus.RUNNING).transition(AgentStatus.COMPLETED))
    assert store.payload("a", "team/svc") == {"n": 1}
    assert (tmp_path / "runs" / "team-svc" / "a.json").is_file()
    manifest = json.loads((tmp_path / "runs" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status_counts"] == {"COMPLETED": 1} and "payload" not in manifest["repositories"]["team/svc"][0]
    again = SharedStore.load(tmp_path / "runs")
    assert again.payload("a", "team/svc") == {"n": 1} and again.run_id == "r1"


def test_supervisor_publishes_states_and_evidence(sample_repo):
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    default_supervisor().run(ctx, only=["quality_analysis"])
    store = ctx.store
    assert {m.agent: m.status for m in store.messages("svc")} == {
        n: "COMPLETED" for n in ("inventory", "deep_analysis", "functional_analysis", "java_analysis", "quality_analysis")}
    assert store.payload("quality_analysis", "svc") == ctx.results["quality_analysis"]
    kinds = {e["kind"] for e in store.evidence("svc")}
    assert {"bug_candidate", "spring_endpoint", "kafka_listener"} <= kinds
    assert all(e["repository"] == "svc" and e["file"] for e in store.evidence("svc"))
    for m in store.messages():
        validate_message(m.to_dict())


def test_required_failure_propagates_and_marks_the_rest_skipped():
    sup = Supervisor([_agent("a", behaviour=_raise(ValueError("boom"))), _agent("b", ["a"])])
    ctx = AnalysisContext(repository="svc")
    with pytest.raises(ValueError):
        sup.run(ctx)
    a, b = ctx.store.get("a", "svc"), ctx.store.get("b", "svc")
    assert a.status == "FAILED" and a.errors[0]["type"] == "ValueError" and a.errors[0]["recoverable"] is False
    assert b.status == "SKIPPED"


def test_optional_failure_or_skip_does_not_abort():
    sup = Supervisor([
        _agent("a"), _agent("opt", ["a"], optional=True, behaviour=_raise(RuntimeError("x"))),
        _agent("skip", optional=True, behaviour=_raise(AgentSkipped("sin configurar"))),
        _agent("child", ["opt"], optional=True), _agent("z", ["a"]),
    ])
    ctx = AnalysisContext(repository="svc")
    results = sup.run(ctx)
    status = {m.agent: m.status for m in ctx.store.messages("svc")}
    assert status == {"a": "COMPLETED", "opt": "FAILED", "skip": "SKIPPED", "child": "SKIPPED", "z": "COMPLETED"}
    assert set(results) == {"a", "z"}
    assert ctx.store.get("skip", "svc").detail == "sin configurar"
    assert ctx.store.errors("svc")[0]["recoverable"] is True


def test_group_run_writes_agent_runs(sample_repo, tmp_path, monkeypatch):
    import app.analysis_orchestrator as orch
    monkeypatch.setattr(orch, "WORKSPACES_DIR", tmp_path)
    monkeypatch.setattr(orch, "clone_repository", lambda *a, **k: sample_repo)
    result = orch.run_group_analysis("g1", "Grupo", [{"name": "team/svc", "git_url": "https://x/y.git"}])
    assert result["agent_runs"]["status_counts"].get("FAILED") is None
    assert (tmp_path / "g1" / "agent-runs" / "manifest.json").is_file()
    assert (tmp_path / "g1" / "agent-runs" / "_group" / "integration_analysis.json").is_file()
    assert (tmp_path / "g1" / "agent-runs" / "team-svc" / "java_analysis.json").is_file()
