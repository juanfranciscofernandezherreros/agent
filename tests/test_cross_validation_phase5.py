from app.agents import AnalysisContext, CrossValidationAgent, GroupCrossValidationAgent
from app.supervisor import default_supervisor
from conftest import FakeLLM


def _by_id(result):
    return {c["id"]: c for c in result["checks"]}


def test_validation_runs_after_llm_agents():
    sup = default_supervisor()
    plan = [a.name for a in sup.plan("repository")]
    assert plan[-1] == "cross_validation"
    assert [a.name for a in sup.plan("group")] == ["integration_analysis", "llm_evidence_correlation", "group_cross_validation"]


def test_static_only_validation_flags_real_gaps_between_analyzers(sample_repo):
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    result = default_supervisor().run(ctx)["cross_validation"]
    checks = _by_id(result)
    assert checks["inventory_vs_java"]["status"] == "consistent"
    assert checks["tests_deep_vs_quality"]["status"] == "consistent"
    assert checks["quality_files"]["status"] == "consistent"
    # El análisis profundo no ve el Kafka ni los endpoints que sí ve el analizador Java.
    assert checks["messaging_java_vs_deep"]["status"] == "warning"
    assert checks["api_java_vs_deep"]["status"] == "warning"
    assert result["status"] == "WARNINGS" and result["summary"]["contradiction"] == 0
    assert not any(k.startswith("llm") or k.startswith("bug_review") for k in checks)
    msg = ctx.store.get("cross_validation", "svc")
    assert msg.status == "COMPLETED" and {e["kind"] for e in msg.evidence} == {"warning"}


def test_contradictions_between_static_agents_are_detected(sample_repo):
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    default_supervisor().run(ctx, only=["quality_analysis"])
    ctx.results["java_analysis"] = {**ctx.results["java_analysis"], "summary": {**ctx.results["java_analysis"]["summary"], "classes": 0}}
    ctx.results["quality_analysis"]["score_factors"]["test_files_detected"] = 7
    ctx.results["quality_analysis"]["bug_candidates"][0]["file"] = "ghost.py"
    checks = _by_id(CrossValidationAgent().run(ctx))
    for cid in ("inventory_vs_java", "tests_deep_vs_quality", "quality_files"):
        assert checks[cid]["status"] == "contradiction", cid
    assert checks["quality_files"]["items"] == [{"file": "ghost.py"}]


def test_consistent_llm_output_passes(sample_repo, fake_llm):
    result = default_supervisor(fake_llm).run(AnalysisContext(root=sample_repo, repository="svc"))["cross_validation"]
    checks = _by_id(result)
    assert checks["bug_review_refs"]["status"] == "consistent"
    assert checks["bug_review_disagreement"]["status"] == "consistent"
    assert checks["llm_citations:llm_functional_interpretation"]["status"] == "consistent"
    assert checks["llm_citations:llm_architecture_explanation"]["status"] == "consistent"
    assert "llm_bug_review" in result["reviewed_agents"]


def test_llm_hallucinations_and_disagreements_are_flagged(sample_repo):
    llm = FakeLLM(overrides={
        '"reviews"': lambda data: {"reviews": [
            {"ref": data[0]["ref"], "verdict": "false_positive", "rationale": "es un test"},
            {"ref": "BUG999@Nope.java:1", "verdict": "likely_bug", "rationale": "inventado"}]},
        '"purpose"': {"purpose": "x", "capabilities": [
            {"name": "Fantasma", "description": "", "evidence": [{"file": "src/Ghost.java", "line": 3}]},
            {"name": "Fuera de rango", "description": "", "evidence": [{"file": "worker.py", "line": 999}]},
            {"name": "Sin cita", "description": "", "evidence": []}]},
        '"overview"': {"overview": "x", "components": [], "risks": [],
                       "integrations": [{"name": "RabbitMQ y Postgres", "type": "database", "description": "", "evidence": []},
                                        {"name": "Kafka", "type": "mensajería", "description": "", "evidence": []}]},
    })
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    result = default_supervisor(llm).run(ctx)["cross_validation"]
    checks = _by_id(result)
    assert result["status"] == "CONTRADICTIONS"
    assert checks["bug_review_refs"]["items"][0]["ref"] == "BUG999@Nope.java:1"
    assert checks["bug_review_coverage"]["status"] == "warning"
    assert checks["bug_review_disagreement"]["status"] == "contradiction"  # high + false_positive
    problems = {i["problem"].split(" (")[0] for i in checks["llm_citations:llm_functional_interpretation"]["items"]}
    assert problems == {"archivo inexistente", "línea fuera de rango"}
    # Kafka y SQL sí tienen respaldo estático en este repo: no es contradicción.
    assert checks["architecture_integrations"]["status"] == "consistent"


def test_unsupported_architecture_integration(tmp_path):
    (tmp_path / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    llm = FakeLLM(overrides={'"overview"': {"overview": "x", "components": [], "risks": [],
                  "integrations": [{"name": "Kafka", "type": "mensajería", "description": "", "evidence": []}]},
                  '"purpose"': {"purpose": "x"}})
    result = default_supervisor(llm).run(AnalysisContext(root=tmp_path, repository="svc"))["cross_validation"]
    assert _by_id(result)["architecture_integrations"]["status"] == "contradiction"


def test_group_validation(sample_repo, tmp_path, monkeypatch):
    import app.analysis_orchestrator as orch
    monkeypatch.setattr(orch, "WORKSPACES_DIR", tmp_path)
    monkeypatch.setattr(orch, "clone_repository", lambda *a, **k: sample_repo)
    llm = FakeLLM(overrides={'"flows"': {"flows": [
        {"description": "ok", "from": "team/svc", "to": "team/svc", "via": "orders.created",
         "evidence": [{"repository": "team/svc", "file": "worker.py", "line": 1}]},
        {"description": "inventado", "from": "billing", "to": "team/svc", "via": "payments.done",
         "evidence": [{"repository": "team/svc", "file": "nope.java", "line": 1}]}]}})
    result = orch.run_group_analysis("g1", "Grupo", [{"name": "team/svc", "git_url": "https://x/y.git"}],
                                     supervisor=default_supervisor(llm))
    validation = result["agent_insights"]["group_cross_validation"]
    checks = _by_id(validation)
    assert checks["topic_endpoints"]["status"] == "warning"  # orders.created solo tiene consumidor
    assert checks["llm_flows"]["status"] == "contradiction"
    assert len(checks["llm_flows"]["items"]) == 3 and all(i["flow"] == "inventado" for i in checks["llm_flows"]["items"])
    assert result["repositories"][0]["agent_insights"]["cross_validation"]["status"] in ("WARNINGS", "CONSISTENT")
    assert result["agent_runs"]["status_counts"].get("FAILED") is None


def test_validation_failure_never_breaks_the_analysis(sample_repo, monkeypatch):
    monkeypatch.setattr(CrossValidationAgent, "run", lambda self, ctx: 1 / 0)
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    results = default_supervisor().run(ctx)
    assert "quality_analysis" in results and "cross_validation" not in results
    assert ctx.store.get("cross_validation", "svc").status == "FAILED"
