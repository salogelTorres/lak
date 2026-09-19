import logging

import pytest

from app.router import NO_THINK, THINK, OllamaRouter, ROUTER_SYSTEM_PROMPT, parse_label


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("THINK", THINK),
        ("NO_THINK", NO_THINK),
        ("no_think", NO_THINK),
        ("No think", NO_THINK),
        ("NO-THINK.", NO_THINK),
        ("  THINK\n", THINK),
        ("Answer: THINK", THINK),
        ("<think>hmm</think>NO_THINK", NO_THINK),
        ('{"label": "THINK"}', THINK),
        ('{\n  "label": "NO_THINK"\n}', NO_THINK),
        ("I don't know", None),
        ("", None),
    ],
)
def test_parse_label(raw, expected):
    assert parse_label(raw) == expected


def test_parse_label_does_not_mistake_no_think_for_think():
    # "THINK" is a substring of "NO_THINK" — order of checks matters.
    assert parse_label("NO_THINK") == NO_THINK
    assert parse_label("NOTHINK") == NO_THINK


class FakeAsyncClient:
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


class FakeResponse:
    def __init__(self, payload, *, error=None):
        self._payload = payload
        self._error = error

    def raise_for_status(self):
        if self._error:
            raise self._error

    def json(self):
        return self._payload


def patch_client(monkeypatch, response):
    import app.router as router_module

    calls: list = []
    monkeypatch.setattr(router_module.httpx, "AsyncClient", lambda **kw: FakeAsyncClient(calls, response))
    return calls


async def test_classify_true_when_router_says_think(monkeypatch):
    patch_client(monkeypatch, FakeResponse({"message": {"content": '{"label": "THINK"}'}}))
    router = OllamaRouter("http://ollama:11434", "qwen3.5:4b")

    assert await router.classify("some tricky question") is True


async def test_classify_false_when_router_says_no_think(monkeypatch):
    patch_client(monkeypatch, FakeResponse({"message": {"content": '{"label": "NO_THINK"}'}}))
    router = OllamaRouter("http://ollama:11434", "qwen3.5:4b")

    assert await router.classify("hola") is False


async def test_classify_sends_expected_payload(monkeypatch):
    calls = patch_client(monkeypatch, FakeResponse({"message": {"content": "NO_THINK"}}))
    router = OllamaRouter("http://ollama:11434/", "qwen3.5:4b", temperature=0.0, timeout=5.0)

    await router.classify("hola")

    url, kwargs = calls[0]
    assert url == "http://ollama:11434/api/chat"
    payload = kwargs["json"]
    assert payload["model"] == "qwen3.5:4b"
    assert payload["messages"] == [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": "hola"},
    ]
    assert payload["think"] is False
    assert payload["format"]["properties"]["label"]["enum"] == ["THINK", "NO_THINK"]
    assert payload["options"] == {"num_predict": 20, "temperature": 0.0}


async def test_classify_fails_open_on_network_error(monkeypatch, caplog):
    def _raise(**kwargs):
        raise RuntimeError("connection refused")

    import app.router as router_module

    monkeypatch.setattr(router_module.httpx, "AsyncClient", _raise)
    router = OllamaRouter("http://ollama:11434", "qwen3.5:4b")

    with caplog.at_level(logging.WARNING, logger="app.router"):
        result = await router.classify("hola")

    assert result is False
    assert "router call failed" in caplog.text.lower()


async def test_classify_fails_open_on_http_error(monkeypatch):
    patch_client(monkeypatch, FakeResponse({}, error=RuntimeError("500")))
    router = OllamaRouter("http://ollama:11434", "qwen3.5:4b")

    assert await router.classify("hola") is False


async def test_classify_fails_open_on_unparseable_response(monkeypatch, caplog):
    patch_client(monkeypatch, FakeResponse({"message": {"content": "I'm not sure"}}))
    router = OllamaRouter("http://ollama:11434", "qwen3.5:4b")

    with caplog.at_level(logging.WARNING, logger="app.router"):
        result = await router.classify("hola")

    assert result is False
    assert "unparseable label" in caplog.text.lower()
