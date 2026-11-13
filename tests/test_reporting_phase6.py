import json
import pytest
from app.agents import AnalysisContext
from app.supervisor import default_supervisor
from conftest import FakeLLM

REPOS = [{"name": "team/orders", "git_url": "https://x/a.git"}, {"name": "team/billing", "git_url": "https://x/b.git"}]


@pytest.fixture
def run(sample_repo, tmp_path, monkeypatch):
    import app.analysis_orchestrator as orch
    monkeypatch.setattr(orch, "WORKSPACES_DIR", tmp_path)
    monkeypatch.setattr(orch, "clone_repository", lambda *a, **k: sample_repo)

    def _run(llm=None, repos=REPOS):
        return orch.run_group_analysis("g1", "Plataforma", repos, supervisor=default_supervisor(llm)), tmp_path / "g1"
    return _run


def test_reporting_agents_run_last():
    sup = default_supervisor()
    assert [a.name for a in sup.plan("repository")][-1] == "repository_report"
    assert [a.name for a in sup.plan("group")][-1] == "group_report"


def test_global_and_individual_reports_are_generated(run):
    result, folder = run()
    expected = ["analysis.json", "analysis.md", "analysis.html", "agents.md", "agents.html", "index.html", "bug-reports/index.html"]
    for slug in ("team-orders", "team-billing"):
        expected += [f"repositories/{slug}/{f}" for f in ("analysis.json", "analysis.md", "analysis.html", "agents.md", "agents.html")]
    expected += ["bug-reports/team-orders-265899.html", "bug-reports/team-billing-eb8970.html"]
    for rel in expected:
        assert (folder / rel).is_file(), rel
    assert [b["file"] for b in result["bug_reports"]] == ["team-orders-265899.html", "team-billing-eb8970.html"]
    runs = result["agent_runs"]
    assert {m["agent"]: m["status"] for m in runs["group"]}["group_report"] == "COMPLETED"
    assert all({m["agent"]: m["status"] for m in ms}["repository_report"] == "COMPLETED" for ms in runs["repositories"].values())
    assert json.loads((folder / "analysis.json").read_text(encoding="utf-8"))["agent_runs"] == runs
    index = (folder / "index.html").read_text(encoding="utf-8")
    assert "agents.html" in index and "repositories/team-orders/agents.html" in index


def test_static_only_report_explains_missing_llm_and_shows_validation(run):
    _, folder = run()
    md = (folder / "repositories" / "team-orders" / "agents.md").read_text(encoding="utf-8")
    assert "No se ejecutó ningún agente LLM" in md and "SKIPPED" in md
    assert "Validación cruzada: Con avisos" in md and "Mensajería detectada" in md
    assert "Interpretación funcional (LLM)" not in md.replace("| Interpretación funcional (LLM) |", "")
    global_md = (folder / "agents.md").read_text(encoding="utf-8")
    assert "Resumen por microservicio" in global_md and "team/billing" in global_md


def test_llm_sections_and_contradictions_reach_the_reports(run):
    llm = FakeLLM(overrides={'"purpose"': {"purpose": "Gestiona <b>pedidos</b>", "capabilities": [
        {"name": "Inventada", "description": "d", "evidence": [{"file": "Ghost.java", "line": 1}]}]}})
    result, folder = run(llm)
    html = (folder / "repositories" / "team-orders" / "agents.html").read_text(encoding="utf-8")
    assert "Gestiona &lt;b&gt;pedidos&lt;/b&gt;" in html and "<b>pedidos</b>" not in html  # salida LLM escapada
    assert "Con contradicciones" in html and "archivo inexistente" in html
    assert "Revisión de bugs (LLM)" in html and "Explicación arquitectónica (LLM)" in html
    global_html = (folder / "agents.html").read_text(encoding="utf-8")
    assert "Flujos entre microservicios (LLM)" in global_html and "Con contradicciones" in global_html
    assert "Con contradicciones" in (folder / "index.html").read_text(encoding="utf-8")
    assert result["completion_status"] == "STATIC_ANALYSIS_COMPLETED"


def test_report_failure_is_reported_as_repository_failure(run, monkeypatch):
    import app.agents.reporting as reporting
    original = reporting.write_individual_reports

    def flaky(dest, name, *a):
        if name == "team/billing":
            raise OSError("disco lleno")
        return original(dest, name, *a)
    monkeypatch.setattr(reporting, "write_individual_reports", flaky)
    result, folder = run()
    assert result["completion_status"] == "PARTIAL_ANALYSIS_COMPLETED"
    assert result["failures"] == [{"repository": "team/billing", "error": "El agente repository_report no generó los informes: disco lleno"}]
    assert "team/billing: El agente repository_report" in (folder / "agents.md").read_text(encoding="utf-8")


def test_reporting_is_skipped_without_output_dir(sample_repo):
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    default_supervisor().run(ctx)
    assert ctx.store.get("repository_report", "svc").status == "SKIPPED"


def test_api_serves_new_reports(run, monkeypatch, tmp_path):
    import app.main as main
    _, folder = run()
    monkeypatch.setattr(main, "WORKSPACES_DIR", tmp_path)
    assert "Informe multiagente" in main.get_analysis_group_agents_html("g1")
    assert "team/orders" in main.get_analysis_group_repository_agents_html("g1", "team-orders")
    assert main.get_analysis_group_agent_runs("g1")["status_counts"]["COMPLETED"] >= 12
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        main.get_analysis_group_repository_agents_html("g1", "../x")
