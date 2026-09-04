import pytest

ENV_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "ALLOWED_USER_IDS",
    "AGENT_NAME",
    "SYSTEM_PROMPT_FILE",
    "TZ",
    "MAX_HISTORY_TOKENS",
    "RECENT_HISTORY_TOKENS",
    "ENABLED_TOOLS",
    "LLM_BACKEND",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "CLOUD_API_BASE_URL",
    "CLOUD_API_KEY",
    "CLOUD_MODEL",
    "WHISPER_MODEL",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    yield
