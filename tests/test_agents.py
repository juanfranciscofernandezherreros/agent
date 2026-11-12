from pathlib import Path
from unittest.mock import patch

from app.agents import (
    AnalysisContext, InventoryAgent, DeepAnalysisAgent,
    FunctionalAnalysisAgent, JavaAnalysisAgent, QualityAnalysisAgent,
    IntegrationAnalysisAgent,
)


def test_repository_analyzers_share_context_and_keep_results(tmp_path: Path):
    context = AnalysisContext(root=tmp_path)
    inventory = {"file_count_scanned": 3}
    deep = {"tests": {"files": []}, "parse_issues": [], "security": {}}
    functional = {"operations": []}
    java = {"classes": []}
    quality = {"score": 90}

    with patch("app.agents.inventory.analyze_repository", return_value=inventory), \
         patch("app.agents.deep.analyze_repository_deep", return_value=deep) as deep_call, \
         patch("app.agents.functional.analyze_functional_behavior", return_value=functional), \
         patch("app.agents.java.analyze_java_repository", return_value=java), \
         patch("app.agents.quality.analyze_quality", return_value=quality) as quality_call:
        assert InventoryAgent().run(context) is inventory
        assert DeepAnalysisAgent().run(context) is deep
        assert FunctionalAnalysisAgent().run(context) is functional
        assert JavaAnalysisAgent().run(context) is java
        assert QualityAnalysisAgent().run(context) is quality

    deep_call.assert_called_once_with(tmp_path, inventory)
    quality_call.assert_called_once_with(tmp_path, deep, functional, java)
    assert context.results == {
        "inventory": inventory,
        "deep_analysis": deep,
        "functional_analysis": functional,
        "java_analysis": java,
        "quality_analysis": quality,
    }


def test_integration_agent_uses_shared_interface_and_correlates_services():
    context = AnalysisContext(data={"repositories": [
        {"name": "producer", "java_analysis": {
            "kafka_producers": [{"expression": 'send("orders.created")', "file": "Producer.java", "line": 10}],
        }},
        {"name": "consumer", "java_analysis": {
            "kafka_listeners": [{"arguments": 'topics = "orders.created"', "file": "Consumer.java", "line": 20}],
        }},
    ]})

    result = IntegrationAnalysisAgent().run(context)

    candidate = result["topic_candidates"][0]
    assert candidate["topic"] == "orders.created"
    assert candidate["repositories"] == ["consumer", "producer"]
    assert candidate["cross_service_candidate"] is True
    assert candidate["producer_and_consumer_candidates"] is True
    assert context.results["integration_analysis"] is result
