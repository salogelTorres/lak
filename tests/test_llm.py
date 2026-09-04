import pytest

from app.config import Config
from app.llm import CloudClient, OllamaClient, build_llm_client


class FakeResponse:
    def __init__(self, payload, *, error=None):
        self._payload = payload
        self._error = error

    def raise_for_status(self):
        if self._error:
            raise self._error

    def json(self):
        return self._payload


class FakeAsyncClient:
    """Records every call made through it; shared across the `with` block."""

    def __init__(self, calls, response):
        self.calls = calls
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def make_config(**overrides) -> Config:
    defaults = dict(
        telegram_token="tok",
        allowed_user_ids=set(),
        agent_name="Assistant",
        system_prompt="",
        timezone="UTC",
        llm_backend="ollama",
        ollama_base_url="http://ollama:11434",
        ollama_model="llama3",
        cloud_api_base_url="https://api.example.com/v1",
        cloud_api_key="sk-test",
        cloud_model="gpt-4o-mini",
        whisper_model="small",
        max_history_tokens=2000,
        recent_history_tokens=500,
    )
    defaults.update(overrides)
    return Config(**defaults)


@pytest.fixture
def patch_async_client(monkeypatch):
    def _patch(module, response):
        calls: list = []
        monkeypatch.setattr(module, "AsyncClient", lambda *a, **kw: FakeAsyncClient(calls, response))
        return calls

    return _patch


def test_ollama_client_read_timeout_tolerates_cold_model_load():
    # A cold model load (nothing in memory/VRAM yet) can take a minute or
    # more before generating a single token; the read timeout must comfortably
    # exceed that on top of generation time, or the very first request after
    # `docker compose up` fails outright.
    assert OllamaClient.TIMEOUT.read >= 200
    assert OllamaClient.TIMEOUT.connect <= 30


async def test_ollama_client_chat(patch_async_client):
    import app.llm as llm_module

    response = FakeResponse({"message": {"content": "hello there"}})
    calls = patch_async_client(llm_module.httpx, response)

    client = OllamaClient("http://ollama:11434/", "llama3")
    messages = [{"role": "user", "content": "hi"}]

    result = await client.chat(messages)

    assert result == "hello there"
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "http://ollama:11434/api/chat"
    assert kwargs["json"] == {"model": "llama3", "messages": messages, "stream": False}


async def test_cloud_client_chat(patch_async_client):
    import app.llm as llm_module

    response = FakeResponse({"choices": [{"message": {"content": "cloud reply"}}]})
    calls = patch_async_client(llm_module.httpx, response)

    client = CloudClient("https://api.example.com/v1/", "sk-test", "gpt-4o-mini")
    messages = [{"role": "user", "content": "hi"}]

    result = await client.chat(messages)

    assert result == "cloud reply"
    url, kwargs = calls[0]
    assert url == "https://api.example.com/v1/chat/completions"
    assert kwargs["headers"] == {"Authorization": "Bearer sk-test"}
    assert kwargs["json"] == {"model": "gpt-4o-mini", "messages": messages}


async def test_client_chat_raises_on_http_error(patch_async_client):
    import app.llm as llm_module

    response = FakeResponse({}, error=RuntimeError("boom"))
    patch_async_client(llm_module.httpx, response)

    client = OllamaClient("http://ollama:11434", "llama3")

    with pytest.raises(RuntimeError, match="boom"):
        await client.chat([{"role": "user", "content": "hi"}])


def test_build_llm_client_ollama():
    config = make_config(llm_backend="ollama")
    client = build_llm_client(config)
    assert isinstance(client, OllamaClient)
    assert client.base_url == "http://ollama:11434"
    assert client.model == "llama3"


def test_build_llm_client_cloud():
    config = make_config(llm_backend="cloud")
    client = build_llm_client(config)
    assert isinstance(client, CloudClient)
    assert client.base_url == "https://api.example.com/v1"
    assert client.api_key == "sk-test"
    assert client.model == "gpt-4o-mini"
