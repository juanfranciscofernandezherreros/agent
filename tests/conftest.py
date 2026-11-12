import pytest


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
