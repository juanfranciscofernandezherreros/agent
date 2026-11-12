from app.rich_report import build_integral_html


def test_integral_report_contains_executive_architecture_and_evidence_sections():
    analysis = {
        "completion_status": "STATIC_ANALYSIS_COMPLETED",
        "runtime_validation": "NOT_PERFORMED",
        "repositories": [{
            "name": "billing-watcher",
            "artifact_dir": "repositories/billing-watcher",
            "inventory": {"commit_sha": "abc123", "languages": {"Java": 12}},
            "deep_analysis": {
                "scan_stats": {"files_seen": 12, "test_files": 2},
                "architecture": {"top_level_directories": ["src"], "entrypoints": ["Application.java"]},
                "dependencies": {"manifests": ["pom.xml"], "package_json_dependencies": []},
                "api": {"route_candidates": []},
                "configuration": {"files": ["application.yml"], "environment_variable_names": ["KAFKA_TOPIC"]},
                "data": {"migration_files": [], "model_candidates": []},
                "security": {},
                "integrations": {},
                "tests": {"files": ["WorkerTest.java"]},
                "parse_issues": [],
                "limitations": [],
            },
            "functional_analysis": {
                "summary": {"operations": 1, "business_rules": 1},
                "operations": [{"name": "process", "file": "Worker.java", "start_line": 10, "confidence": "medium"}],
                "business_rules": [], "validations": [], "error_handling": [], "state_changes": [],
                "limitations": [],
            },
            "quality_analysis": {"score": 82, "rating": "Mejorable", "summary": {"bug_candidates": 2, "high": 1, "medium": 1}, "bug_candidates": [{"code": "BUG004", "severity": "high", "title": "Uso de assert", "file": "Worker.java", "line": 12, "excerpt": "assert id != null", "description": "Revisar validación"}]},
            "java_analysis": {
                "summary": {"classes": 1, "methods": 1, "sql_statements": 0, "kafka_listeners": 1, "kafka_producers": 1, "avro_contracts": 0},
                "classes": [{"name": "Worker", "kind": "class", "file": "Worker.java", "line": 1}],
                "methods": [{"name": "process", "class_name": "Worker", "parameters": "String id", "file": "Worker.java", "line": 10, "end_line": 20, "calls": ["save"], "branches_and_errors": [], "possible_effects": ["publish"], "confidence": "inferred"}],
                "call_references": [{"caller": "process", "callee": "save", "file": "Worker.java", "line": 10, "confidence": "inferred"}],
                "injections": [], "spring_endpoints": [], "kafka_listeners": [], "kafka_producers": [],
                "configuration_keys": [], "sql_statements": [], "avro_contracts": [],
                "limitations": [],
            },
        }],
        "integration_analysis": {
            "topic_candidates": [{
                "topic": "billing.events", "repositories": ["billing-watcher"],
                "roles_detected": ["consumer_candidate", "producer_candidate"],
                "producer_and_consumer_candidates": True, "cross_service_candidate": False,
                "evidence": [{"repository": "billing-watcher", "role": "consumer_candidate", "file": "Worker.java", "line": 10}],
            }],
            "shared_contract_candidates": [],
            "producer_candidates": [{"repository": "billing-watcher", "expression": "KafkaTemplate.send", "file": "Worker.java", "line": 15}],
            "limitations": [],
        },
        "failures": [],
    }

    report = build_integral_html("Billing platform", analysis)

    assert "Resumen ejecutivo" in report
    assert "Alcance, método y cobertura" in report
    assert "Mapa de servicios" in report
    assert "Topics Kafka candidatos" in report
    assert "Expresiones productoras Kafka detectadas" in report
    assert "billing.events" in report
    assert "Worker" in report
    assert "process(String id)" in report
    assert "Riesgos técnicos y plan de validación" in report
    assert "Calidad estática: Mejorable" in report
    assert "Posibles bugs detectados" in report
    assert "Puntuación /100" in report


def test_integral_report_escapes_untrusted_repository_names():
    report = build_integral_html("<script>alert(1)</script>", {
        "repositories": [],
        "integration_analysis": {},
        "failures": [],
    })

    assert "<script>alert(1)</script>" not in report
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report
