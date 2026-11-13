import httpx
import pytest
from app import llm
from app.llm import LLMClient, LLMError, build_chat_model, list_models, settings_from_env, status


def _env(monkeypatch, **values):
    for key, value in values.items():
        monkeypatch.setenv(key, value)


@pytest.mark.parametrize("provider,key_env,model,cls", [
    ("openai", "OPENAI_API_KEY", "gpt-x", "ChatOpenAI"),
    ("claude", "ANTHROPIC_API_KEY", "claude-x", "ChatAnthropic"),
    ("gemini", "GOOGLE_API_KEY", "gemini-x", "ChatGoogleGenerativeAI"),
    ("ollama", None, "qwen2.5-coder:14b", "ChatOllama"),
])
def test_each_provider_builds_its_langchain_model(monkeypatch, provider, key_env, model, cls):
    pytest.importorskip("langchain")
    _env(monkeypatch, LLM_PROVIDER=provider, LLM_MODEL=model)
    if key_env:
        _env(monkeypatch, **{key_env: "secret-key"})
    settings = settings_from_env()
    assert (settings.provider, settings.model) == (provider, model)
    chat = build_chat_model(settings)
    assert type(chat).__name__ == cls
    assert "secret-key" not in str(settings.public())


def test_aliases_key_fallback_and_errors(monkeypatch):
    _env(monkeypatch, LLM_PROVIDER="Anthropic", LLM_MODEL="m", LLM_API_KEY="generic")
    assert settings_from_env().provider == "claude" and settings_from_env().api_key == "generic"
    _env(monkeypatch, ANTHROPIC_API_KEY="specific")
    assert settings_from_env().api_key == "specific"  # la clave específica tiene prioridad
    _env(monkeypatch, LLM_PROVIDER="gemini")
    monkeypatch.delenv("LLM_API_KEY")
    with pytest.raises(LLMError, match="GOOGLE_API_KEY"):
        settings_from_env()
    _env(monkeypatch, LLM_PROVIDER="mistral")
    with pytest.raises(LLMError, match="openai, claude, gemini, ollama"):
        settings_from_env()
    _env(monkeypatch, LLM_PROVIDER="ollama")
    monkeypatch.delenv("LLM_MODEL")
    with pytest.raises(LLMError, match="LLM_MODEL"):
        settings_from_env()


def test_base_url_rules(monkeypatch):
    # Una URL de OpenAI olvidada en .env no afecta a otros proveedores.
    _env(monkeypatch, LLM_MODEL="m", LLM_API_KEY="k", LLM_BASE_URL="https://api.openai.com/v1")
    for provider, expected in (("claude", "https://api.anthropic.com"), ("gemini", "https://generativelanguage.googleapis.com"),
                               ("ollama", "http://127.0.0.1:11434"), ("openai", "https://api.openai.com/v1")):
        _env(monkeypatch, LLM_PROVIDER=provider)
        assert settings_from_env().base_url == expected
    # Configuración antigua de Ollama con /v1: se usa la URL raíz.
    _env(monkeypatch, LLM_PROVIDER="ollama", LLM_BASE_URL="http://127.0.0.1:11434/v1")
    assert settings_from_env().base_url == "http://127.0.0.1:11434"
    _env(monkeypatch, OLLAMA_BASE_URL="http://servidor:11434")
    assert settings_from_env().base_url == "http://servidor:11434"
    _env(monkeypatch, LLM_PROVIDER="openai", LLM_BASE_URL="https://mi-proxy/v1/")
    assert settings_from_env().base_url == "https://mi-proxy/v1"


def test_status_never_exposes_keys(monkeypatch):
    assert status()["active"] is False and status()["enabled"] is False
    _env(monkeypatch, LLM_AGENTS_ENABLED="true", LLM_PROVIDER="claude", LLM_MODEL="claude-x")
    info = status()
    assert info["configured"] is False and "ANTHROPIC_API_KEY" in info["problem"] and info["active"] is False
    _env(monkeypatch, ANTHROPIC_API_KEY="muy-secreta")
    info = status()
    assert info["active"] and info["provider"] == "claude" and info["model"] == "claude-x"
    assert "muy-secreta" not in str(info) and set(info["providers"]) == {"openai", "claude", "gemini", "ollama"}


class FakeChat:
    def __init__(self, content=None, error=None):
        self.content, self.error, self.messages = content, error, None

    def invoke(self, messages):
        self.messages = messages
        if self.error:
            raise self.error

        class Message:
            content = self.content
        return Message()


def _client(monkeypatch, chat):
    _env(monkeypatch, LLM_PROVIDER="claude", LLM_MODEL="claude-x", ANTHROPIC_API_KEY="k")
    return LLMClient(settings_from_env(), chat=chat)


def test_complete_json_handles_string_and_block_content(monkeypatch):
    chat = FakeChat('```json\n{"ok": true}\n```')
    assert _client(monkeypatch, chat).complete_json("t", "{}", {"password": "hunter2hunter2"}) == {"ok": True}
    assert chat.messages[0][0] == "system" and "NO CONFIABLE" in chat.messages[0][1]
    assert "hunter2hunter2" not in chat.messages[1][1]  # secretos redactados antes de enviar
    blocks = FakeChat([{"type": "thinking", "thinking": "..."}, {"type": "text", "text": '{"a": '}, {"type": "text", "text": "1}"}])
    assert _client(monkeypatch, blocks).complete_json("t", "{}", {}) == {"a": 1}


def test_provider_errors_become_llm_errors(monkeypatch):
    with pytest.raises(LLMError, match="Claude.*claude-x.*RuntimeError: 401"):
        _client(monkeypatch, FakeChat(error=RuntimeError("401 clave inválida"))).complete_json("t", "{}", {})
    with pytest.raises(LLMError):
        _client(monkeypatch, FakeChat("esto no es JSON")).complete_json("t", "{}", {})


def test_list_models_per_provider(monkeypatch):
    seen = []

    def handler(request):
        seen.append((str(request.url), dict(request.headers)))
        host, path = request.url.host, request.url.path
        if host == "api.openai.com":
            return httpx.Response(200, json={"data": [{"id": "gpt-b"}, {"id": "gpt-a"}]})
        if host == "api.anthropic.com":
            return httpx.Response(200, json={"data": [{"id": "claude-a"}]})
        if host == "generativelanguage.googleapis.com":
            return httpx.Response(200, json={"models": [
                {"name": "models/gemini-a", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/embedding-x", "supportedGenerationMethods": ["embedContent"]}]})
        if path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen2.5-coder:14b"}]})
        return httpx.Response(404)
    real = httpx.Client
    monkeypatch.setattr(llm.httpx, "Client", lambda **k: real(transport=httpx.MockTransport(handler), **k))
    _env(monkeypatch, OPENAI_API_KEY="ok", ANTHROPIC_API_KEY="ak", GOOGLE_API_KEY="gk")
    assert list_models(provider="openai") == ["gpt-a", "gpt-b"]
    assert list_models(provider="claude") == ["claude-a"]
    assert list_models(provider="gemini") == ["gemini-a"]
    assert list_models(provider="ollama") == ["qwen2.5-coder:14b"]
    assert all("ok" not in url and "ak" not in url and "gk" not in url for url, _ in seen)  # claves solo en cabeceras
    assert seen[2][1]["x-goog-api-key"] == "gk" and seen[1][1]["x-api-key"] == "ak"
    monkeypatch.delenv("GOOGLE_API_KEY")
    with pytest.raises(LLMError, match="GOOGLE_API_KEY"):
        list_models(provider="gemini")


def test_changing_model_invalidates_the_cache(monkeypatch):
    from app import analysis_cache
    assert analysis_cache._signature("c")["llm_agents"] is False
    _env(monkeypatch, LLM_AGENTS_ENABLED="true", LLM_PROVIDER="ollama", LLM_MODEL="a")
    first = analysis_cache._signature("c")
    _env(monkeypatch, LLM_MODEL="b")
    assert first["llm_agents"] == "ollama:a" and analysis_cache._signature("c") != first


def test_agents_use_the_configured_provider_end_to_end(sample_repo, monkeypatch):
    """Sin cliente inyectado: los agentes crean el suyo desde el entorno y pasan por LangChain."""
    from app.agents import AnalysisContext
    from app.supervisor import default_supervisor
    _env(monkeypatch, LLM_AGENTS_ENABLED="true", LLM_PROVIDER="gemini", LLM_MODEL="gemini-x", GOOGLE_API_KEY="k")
    monkeypatch.setattr(llm, "build_chat_model", lambda settings: FakeChat('{"purpose": "Gestiona pedidos", "overview": "Servicio", "reviews": []}'))
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    results = default_supervisor().run(ctx)
    functional = results["llm_functional_interpretation"]
    assert functional["purpose"] == "Gestiona pedidos" and functional["provider"] == "gemini" and functional["model"] == "gemini-x"
    assert ctx.store.get("llm_architecture_explanation", "svc").status == "COMPLETED"


def test_skip_reason_explains_what_is_missing(sample_repo, monkeypatch):
    from app.agents import AnalysisContext
    from app.supervisor import default_supervisor
    _env(monkeypatch, LLM_AGENTS_ENABLED="true", LLM_PROVIDER="claude", LLM_MODEL="claude-x")
    ctx = AnalysisContext(root=sample_repo, repository="svc")
    default_supervisor().run(ctx)
    assert "ANTHROPIC_API_KEY" in ctx.store.get("llm_functional_interpretation", "svc").detail
