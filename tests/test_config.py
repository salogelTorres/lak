import pytest

from app.config import Config, _split_ids


def test_load_raises_without_token():
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        Config.load()


def test_load_defaults(monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Hi, I'm {{AGENT_NAME}}.", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc123")
    monkeypatch.setenv("SYSTEM_PROMPT_FILE", str(prompt_file))

    config = Config.load()

    assert config.telegram_token == "abc123"
    assert config.agent_name == "Assistant"
    assert config.system_prompt == "Hi, I'm Assistant."
    assert config.allowed_user_ids == set()
    assert config.timezone == "UTC"
    assert config.llm_backend == "ollama"
    assert config.ollama_base_url == "http://host.docker.internal:11434"
    assert config.ollama_model == "qwen3:8b"
    assert config.cloud_api_base_url == "https://api.openai.com/v1"
    assert config.cloud_api_key == ""
    assert config.cloud_model == "gpt-4o-mini"
    assert config.whisper_model == "small"
    assert config.max_history_tokens == 2000


def test_load_custom_values(monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("You are {{AGENT_NAME}}.", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("AGENT_NAME", "Rex")
    monkeypatch.setenv("SYSTEM_PROMPT_FILE", str(prompt_file))
    monkeypatch.setenv("ALLOWED_USER_IDS", "1, 2,3")
    monkeypatch.setenv("LLM_BACKEND", "CLOUD")
    monkeypatch.setenv("CLOUD_API_KEY", "sk-test")
    monkeypatch.setenv("TZ", "Europe/Madrid")
    monkeypatch.setenv("WHISPER_MODEL", "medium")
    monkeypatch.setenv("MAX_HISTORY_TOKENS", "8000")

    config = Config.load()

    assert config.agent_name == "Rex"
    assert config.system_prompt == "You are Rex."
    assert config.allowed_user_ids == {1, 2, 3}
    assert config.llm_backend == "cloud"
    assert config.cloud_api_key == "sk-test"
    assert config.timezone == "Europe/Madrid"
    assert config.whisper_model == "medium"
    assert config.max_history_tokens == 8000


def test_load_invalid_max_history_tokens(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("MAX_HISTORY_TOKENS", "not-a-number")

    with pytest.raises(RuntimeError, match="Invalid MAX_HISTORY_TOKENS"):
        Config.load()


def test_load_blank_timezone_defaults_to_utc(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TZ", "   ")

    config = Config.load()

    assert config.timezone == "UTC"


def test_load_missing_prompt_file_is_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("SYSTEM_PROMPT_FILE", str(tmp_path / "does-not-exist.txt"))

    config = Config.load()

    assert config.system_prompt == ""


def test_load_invalid_backend(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("LLM_BACKEND", "bogus")

    with pytest.raises(RuntimeError, match="Invalid LLM_BACKEND"):
        Config.load()


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", set()),
        ("1", {1}),
        ("1,2,3", {1, 2, 3}),
        ("1,,2", {1, 2}),
        (" 1 , 2 ", {1, 2}),
    ],
)
def test_split_ids(raw, expected):
    assert _split_ids(raw) == expected
