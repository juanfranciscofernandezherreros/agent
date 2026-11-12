import json
from app.agents import AnalysisContext
from app.communication import validate_message
from app.supervisor import default_supervisor
from conftest import FakeLLM

LLM_REPO = ("llm_functional_interpretation", "llm_bug_review", "llm_architecture_explanation")


def test_llm_agents_are_skipped_without_configuration(sample_repo, monkeypatch):
    monkeypatch.delenv("LLM_AGENTS_ENABLED", raising=False)
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    results = default_supervisor().run(ctx)
    assert not any(k.startswith("llm_") for k in results)
    for name in LLM_REPO:
        msg = ctx.store.get(name, "svc")
        assert msg.status == "SKIPPED" and "LLM" in msg.detail
    assert ctx.store.get("quality_analysis", "svc").status == "COMPLETED"


def test_enabled_flag_alone_is_not_enough(monkeypatch):
    from app.llm import LLMClient
    monkeypatch.setenv("LLM_AGENTS_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert LLMClient.from_env() is None
    monkeypatch.setenv("LLM_API_KEY", "k")
    assert LLMClient.from_env().model


def test_llm_agents_produce_normalised_payloads_and_evidence(sample_repo, fake_llm):
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    results = default_supervisor(fake_llm).run(ctx)
    assert results["llm_functional_interpretation"]["purpose"] == "Gestiona pedidos"
    assert results["llm_architecture_explanation"]["components"][0]["evidence"][0]["file"].endswith(".java")
    review = results["llm_bug_review"]
    assert review["summary"]["reviewed"] == results["quality_analysis"]["summary"]["bug_candidates"]
    for name in LLM_REPO:
        assert results[name]["confidence"] == "llm_inferred" and results[name]["model"] == "fake-model"
        msg = ctx.store.get(name, "svc")
        assert msg.status == "COMPLETED" and msg.evidence
        assert all(e["confidence"] == "llm_inferred" for e in msg.evidence)
        validate_message(msg.to_dict())
    # El contexto de código enviado incluye la línea señalada, con su número.
    bug_call = next(c for c in fake_llm.calls if '"reviews"' in c["schema"])
    assert any("assert x" in x["context"] for x in bug_call["data"])


def test_malformed_llm_output_is_normalised(sample_repo):
    llm = FakeLLM(overrides={
        '"reviews"': {"reviews": [{"ref": "X@y:1", "verdict": "DEFINITELY"}, "junk", {"verdict": "likely_bug"}]},
        '"purpose"': {"purpose": 5, "capabilities": "no-list", "business_rules": [{"rule": "r", "evidence": [{"line": 3}, {"file": "a.java", "line": "x"}]}]},
    })
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    results = default_supervisor(llm).run(ctx)
    assert results["llm_bug_review"]["reviews"] == [
        {"ref": "X@y:1", "verdict": "needs_review", "rationale": "", "suggested_fix": ""}]
    f = results["llm_functional_interpretation"]
    assert f["purpose"] == "5" and f["capabilities"] == []
    assert f["business_rules"][0]["evidence"] == [{"file": "a.java", "line": None}]


def test_llm_failure_does_not_break_static_analysis(sample_repo):
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    results = default_supervisor(FakeLLM(fail_on='"overview"')).run(ctx)
    msg = ctx.store.get("llm_architecture_explanation", "svc")
    assert msg.status == "FAILED" and msg.errors[0]["recoverable"] is True
    assert "quality_analysis" in results and "llm_functional_interpretation" in results


def test_secrets_are_redacted_before_reaching_the_llm(sample_repo):
    (sample_repo / "cfg.py").write_text('password = "hunter2hunter2"\n', encoding="utf-8")
    llm = FakeLLM()
    default_supervisor(llm).run(AnalysisContext(root=sample_repo, repository="svc"))
    from app.llm import render
    assert "hunter2hunter2" not in "".join(render(c["data"]) for c in llm.calls)


def test_group_flow_with_llm(sample_repo, tmp_path, monkeypatch, fake_llm):
    import app.analysis_orchestrator as orch
    monkeypatch.setattr(orch, "WORKSPACES_DIR", tmp_path)
    monkeypatch.setattr(orch, "clone_repository", lambda *a, **k: sample_repo)
    result = orch.run_group_analysis("g1", "Grupo", [{"name": "team/svc", "git_url": "https://x/y.git"}],
                                     supervisor=default_supervisor(fake_llm))
    assert result["agent_insights"]["llm_evidence_correlation"]["flows"][0]["via"]
    assert set(LLM_REPO) <= set(result["repositories"][0]["agent_insights"])
    saved = json.loads((tmp_path / "g1" / "repositories" / "team-svc" / "analysis.json").read_text(encoding="utf-8"))
    assert saved["agent_insights"]["llm_functional_interpretation"]["purpose"] == "Gestiona pedidos"
