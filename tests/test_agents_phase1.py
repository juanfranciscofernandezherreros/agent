"""Fase 1: los adaptadores conservan exactamente la lógica de los analizadores."""
from app.agents import (
    AnalysisContext, InventoryAgent, DeepAnalysisAgent, FunctionalAnalysisAgent,
    JavaAnalysisAgent, QualityAnalysisAgent, IntegrationAnalysisAgent,
)
from app.agents.context import AnalyzerAgent
from app.engines import analyze_repository
from app.deep_analysis import analyze_repository_deep
from app.functional_analysis import analyze_functional_behavior
from app.java_analysis import analyze_java_repository
from app.quality_analysis import analyze_quality
from app.integration_analysis import correlate

ALL = [InventoryAgent, DeepAnalysisAgent, FunctionalAnalysisAgent,
       JavaAnalysisAgent, QualityAnalysisAgent, IntegrationAnalysisAgent]


def test_all_agents_share_the_common_interface():
    names = set()
    for cls in ALL:
        agent = cls()
        assert isinstance(agent, AnalyzerAgent)
        assert agent.name != "unnamed" and agent.name not in names
        assert agent.scope in {"repository", "group"}
        assert isinstance(agent.requires, tuple)
        names.add(agent.name)
    assert IntegrationAnalysisAgent.scope == "group"


def test_adapters_return_exactly_what_the_original_functions_return(sample_repo):
    inv = analyze_repository(sample_repo)
    deep = analyze_repository_deep(sample_repo, inv)
    functional = analyze_functional_behavior(sample_repo)
    java = analyze_java_repository(sample_repo)
    quality = analyze_quality(sample_repo, deep, functional, java)

    ctx = AnalysisContext(root=sample_repo)
    assert InventoryAgent().run(ctx) == inv
    assert DeepAnalysisAgent().run(ctx) == deep
    assert FunctionalAnalysisAgent().run(ctx) == functional
    assert JavaAnalysisAgent().run(ctx) == java
    assert QualityAnalysisAgent().run(ctx) == quality
    assert set(ctx.results) == {"inventory", "deep_analysis", "functional_analysis",
                                "java_analysis", "quality_analysis"}

    repos = [{"name": "svc", "java_analysis": java}]
    gctx = AnalysisContext(data={"repositories": repos})
    assert IntegrationAnalysisAgent().run(gctx) == correlate(repos)
    assert java["summary"]["classes"] >= 2 and quality["summary"]["bug_candidates"] >= 1
