import pytest


@pytest.fixture(autouse=True)
def _llm_agents_off(monkeypatch):
    """Las pruebas nunca llaman a un LLM real salvo que inyecten un cliente falso."""
    for name in ("LLM_AGENTS_ENABLED", "LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL", "OLLAMA_BASE_URL",
                 "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "LLM_TEMPERATURE", "LLM_MAX_TOKENS"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def sample_repo(tmp_path):
    """Repositorio mínimo con Java, Python, SQL y configuración Kafka."""
    root = tmp_path / "svc"
    java = root / "src" / "main" / "java" / "com" / "acme"
    java.mkdir(parents=True)
    (java / "OrderController.java").write_text(
        'package com.acme;\n'
        'import org.springframework.web.bind.annotation.*;\n'
        '@RestController\n'
        'public class OrderController {\n'
        '    @Autowired\n'
        '    private OrderService service;\n'
        '    @GetMapping("/orders")\n'
        '    public String list() {\n'
        '        // TODO paginate\n'
        '        if (service == null) { throw new IllegalStateException("x"); }\n'
        '        return service.findAll();\n'
        '    }\n'
        '    @KafkaListener(topics = "orders.created")\n'
        '    public void onOrder(String payload) { service.save(payload); }\n'
        '}\n', encoding="utf-8")
    (java / "OrderService.java").write_text(
        'package com.acme;\n'
        'public class OrderService {\n'
        '    private KafkaTemplate<String, String> template;\n'
        '    public String findAll() { return "SELECT id FROM orders"; }\n'
        '    public void save(String p) { template.send("orders.processed", p); }\n'
        '}\n', encoding="utf-8")
    (root / "worker.py").write_text(
        "def handle(x):\n    assert x\n    return x\n", encoding="utf-8")
    (root / "schema.sql").write_text("CREATE TABLE orders (id INT);\n", encoding="utf-8")
    (root / "pom.xml").write_text("<project/>\n", encoding="utf-8")
    return root


class FakeLLM:
    """Cliente LLM de prueba: responde según el esquema pedido, sin red."""
    model = "fake-model"
    provider = "fake"

    def __init__(self, overrides=None, fail_on=None):
        self.calls, self.overrides, self.fail_on = [], overrides or {}, fail_on

    def complete_json(self, task, schema, data, max_tokens=3000):
        self.calls.append({"task": task, "schema": schema, "data": data})
        if self.fail_on and self.fail_on in schema:
            raise RuntimeError("LLM caído")
        for key, value in self.overrides.items():
            if key in schema:
                return value(data) if callable(value) else value
        if '"reviews"' in schema:
            return {"reviews": [{"ref": x["ref"], "verdict": "needs_review", "rationale": "revisar", "suggested_fix": ""} for x in data]}
        if '"purpose"' in schema:
            ep = data["spring_endpoints"][0]
            return {"purpose": "Gestiona pedidos", "capabilities": [{"name": "Listar pedidos", "description": "GET /orders",
                    "evidence": [{"file": ep["file"], "line": ep["line"]}]}], "business_rules": [], "open_questions": ["¿Paginación?"]}
        if '"overview"' in schema:
            cls = data["classes"][0]
            return {"overview": "Servicio Spring", "components": [{"name": cls["name"], "responsibility": "API",
                    "evidence": [{"file": cls["file"], "line": cls["line"]}]}], "integrations": [], "risks": ["Sin tests"]}
        if '"flows"' in schema:
            t = data["topic_candidates"][0]; e = t["evidence"][0]
            return {"flows": [{"description": "Flujo " + t["topic"], "from": e["repository"], "to": e["repository"], "via": t["topic"],
                    "confidence": "media", "evidence": [{"repository": e["repository"], "file": e["file"], "line": e["line"]}]}], "observations": []}
        return {}


@pytest.fixture
def fake_llm():
    return FakeLLM()
