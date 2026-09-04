import pytest

from app.config import Config
from app.llm import CloudClient, OllamaClient, _call_tool, build_llm_client
from app.tools.base import Tool


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
        enabled_tools=[],
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


class FakeAsyncClientSequence:
    """Like FakeAsyncClient, but returns a different response per call —
    needed to test a multi-round tool-calling exchange."""

    def __init__(self, calls, responses_iter):
        self.calls = calls
        self._responses = responses_iter

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return next(self._responses)


@pytest.fixture
def patch_async_client_sequence(monkeypatch):
    def _patch(module, responses):
        # Each round in the tool-calling loop opens its own `async with
        # httpx.AsyncClient(...)`, so the patched constructor runs once per
        # round — the response iterator must be created here, once, and
        # shared across those calls, not re-created (and reset) every time.
        calls: list = []
        responses_iter = iter(responses)
        monkeypatch.setattr(module, "AsyncClient", lambda *a, **kw: FakeAsyncClientSequence(calls, responses_iter))
        return calls

    return _patch


def make_tool_call(call_id: str, name: str, arguments: str) -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


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


def make_greet_tool(execute=None):
    return Tool(
        name="greet",
        description="Greets someone by name",
        parameters={"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}},
        execute=execute or (lambda name: f"Greeted {name}"),
    )


async def test_ollama_client_executes_tool_call_then_returns_final_reply(patch_async_client_sequence):
    import app.llm as llm_module

    responses = [
        FakeResponse({"message": {"content": None, "tool_calls": [make_tool_call("call1", "greet", '{"name": "Luis"}')]}}),
        FakeResponse({"message": {"content": "Hello, Luis!"}}),
    ]
    calls = patch_async_client_sequence(llm_module.httpx, responses)
    tool = make_greet_tool()
    client = OllamaClient("http://ollama:11434", "llama3")

    result = await client.chat([{"role": "user", "content": "greet Luis"}], tools=[tool])

    assert result == "Hello, Luis!"
    assert len(calls) == 2
    _, first_kwargs = calls[0]
    assert first_kwargs["json"]["tools"] == [tool.schema()]
    _, second_kwargs = calls[1]
    sent_messages = second_kwargs["json"]["messages"]
    assert sent_messages[-1] == {"role": "tool", "tool_call_id": "call1", "content": "Greeted Luis"}


async def test_cloud_client_executes_tool_call_then_returns_final_reply(patch_async_client_sequence):
    import app.llm as llm_module

    responses = [
        FakeResponse(
            {"choices": [{"message": {"content": None, "tool_calls": [make_tool_call("call1", "greet", '{"name": "Luis"}')]}}]}
        ),
        FakeResponse({"choices": [{"message": {"content": "Hello, Luis!"}}]}),
    ]
    calls = patch_async_client_sequence(llm_module.httpx, responses)
    tool = make_greet_tool()
    client = CloudClient("https://api.example.com/v1", "sk-test", "gpt-4o-mini")

    result = await client.chat([{"role": "user", "content": "greet Luis"}], tools=[tool])

    assert result == "Hello, Luis!"
    _, first_kwargs = calls[0]
    assert first_kwargs["json"]["tools"] == [tool.schema()]
    assert first_kwargs["json"]["tool_choice"] == "auto"


async def test_chat_without_tools_never_sends_a_tools_field(patch_async_client):
    import app.llm as llm_module

    response = FakeResponse({"message": {"content": "hi"}})
    calls = patch_async_client(llm_module.httpx, response)
    client = OllamaClient("http://ollama:11434", "llama3")

    await client.chat([{"role": "user", "content": "hi"}], tools=[])

    assert "tools" not in calls[0][1]["json"]


async def test_run_with_tools_gives_up_after_max_rounds(patch_async_client_sequence):
    import app.llm as llm_module

    keeps_calling_tools = FakeResponse(
        {"message": {"content": None, "tool_calls": [make_tool_call("c", "greet", '{"name": "Luis"}')]}}
    )
    calls = patch_async_client_sequence(llm_module.httpx, [keeps_calling_tools] * 4)
    tool = make_greet_tool()
    client = OllamaClient("http://ollama:11434", "llama3")

    result = await client.chat([{"role": "user", "content": "hi"}], tools=[tool])

    assert "couldn't get to an answer" in result
    assert len(calls) == 4  # MAX_TOOL_ROUNDS + 1, the last one offered no tools
    assert "tools" not in calls[-1][1]["json"]


async def test_call_tool_reports_unknown_tool_name():
    message = await _call_tool({}, make_tool_call("call1", "mystery", "{}"))

    assert message == {"role": "tool", "tool_call_id": "call1", "content": "Unknown tool: mystery"}


async def test_call_tool_defaults_arguments_on_invalid_json():
    received = {}

    def record(**kwargs):
        received.update(kwargs)
        return "ok"

    tool = Tool(name="t", description="d", parameters={}, execute=record)

    await _call_tool({"t": tool}, make_tool_call("call1", "t", "not json"))

    assert received == {}


async def test_call_tool_catches_execution_errors_instead_of_raising():
    def _raise(**kwargs):
        raise RuntimeError("nope")

    tool = Tool(name="boom", description="d", parameters={}, execute=_raise)

    message = await _call_tool({"boom": tool}, make_tool_call("call1", "boom", "{}"))

    assert message["role"] == "tool"
    assert message["tool_call_id"] == "call1"
    assert "failed" in message["content"].lower()
