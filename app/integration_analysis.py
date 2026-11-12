import re


def correlate(repositories):
    topics, contracts = {}, {}
    producer_evidence = []
    for repo in repositories:
        ja = repo.get("java_analysis", {})
        service = repo.get("name", "unknown")

        for item in ja.get("configuration_keys", []):
            topic = item.get("value")
            if topic:
                topics.setdefault(topic, []).append({
                    "repository": service, "role": "configuration",
                    "file": item.get("file"), "line": item.get("line"),
                    "evidence": item.get("value"), "kind": item.get("kind")
                })

        for item in ja.get("kafka_listeners", []):
            args = item.get("arguments", "")
            literals = re.findall(r"[\"']([^\"']+)[\"']", args)
            for topic in literals:
                topics.setdefault(topic, []).append({
                    "repository": service, "role": "consumer_candidate",
                    "file": item.get("file"), "line": item.get("line"),
                    "evidence": args
                })

        for item in ja.get("kafka_producers", []):
            expression = item.get("expression", "")
            producer_evidence.append({
                "repository": service, "file": item.get("file"),
                "line": item.get("line"), "expression": expression
            })
            literals = re.findall(r"[\"']([^\"']+)[\"']", expression)
            for topic in literals:
                if topic and len(topic) < 250:
                    topics.setdefault(topic, []).append({
                        "repository": service, "role": "producer_candidate",
                        "file": item.get("file"), "line": item.get("line"),
                        "evidence": expression
                    })

        for item in ja.get("avro_contracts", []):
            contract = item.get("name")
            if contract:
                contracts.setdefault(contract, []).append({
                    "repository": service, "file": item.get("file"),
                    "line": item.get("line"), "format": item.get("format")
                })

    topic_candidates = []
    for topic, evidence in sorted(topics.items()):
        unique = {}
        for item in evidence:
            key = (item.get("repository"), item.get("role"), item.get("file"), item.get("line"))
            unique[key] = item
        evidence = list(unique.values())
        services = sorted({item["repository"] for item in evidence})
        roles = sorted({item.get("role", "unknown") for item in evidence})
        topic_candidates.append({
            "topic": topic, "evidence": evidence, "repositories": services,
            "roles_detected": roles,
            "cross_service_candidate": len(services) > 1,
            "producer_and_consumer_candidates": "producer_candidate" in roles and "consumer_candidate" in roles
        })

    shared_contracts = []
    for contract, evidence in sorted(contracts.items()):
        services = sorted({item["repository"] for item in evidence})
        shared_contracts.append({
            "contract": contract, "evidence": evidence, "repositories": services,
            "cross_service_candidate": len(services) > 1
        })

    return {
        "topic_candidates": topic_candidates,
        "shared_contract_candidates": shared_contracts,
        "producer_candidates": producer_evidence,
        "limitations": [
            "La correlación de topics combina valores literales de configuración, anotaciones de consumidores y expresiones de productores; las expresiones dinámicas pueden no resolverse.",
            "Una coincidencia de topic y la presencia de productor/consumidor candidatos no demuestra que estén conectados en el despliegue ni que compartan el mismo tipo de payload.",
            "Los topics definidos mediante placeholders, perfiles externos, constantes indirectas o configuración remota pueden no detectarse.",
            "Los contratos se agrupan por nombre; no se comparan namespaces, campos, tipos, defaults, nullability ni reglas de compatibilidad.",
            "No se deducen garantías de entrega, orden, atomicidad, idempotencia ni semántica de negocio solo por compartir un topic."
        ]
    }
