from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _split_ids(raw: str) -> set[int]:
    return {int(x) for x in raw.split(",") if x.strip()}


@dataclass
class Config:
    telegram_token: str
    allowed_user_ids: set[int]
    agent_name: str
    system_prompt: str
    timezone: str
    llm_backend: str
    ollama_base_url: str
    ollama_model: str
    cloud_api_base_url: str
    cloud_api_key: str
    cloud_model: str
    whisper_model: str

    @classmethod
    def load(cls) -> "Config":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set. Check your .env file."
            )

        agent_name = os.environ.get("AGENT_NAME", "Assistant").strip()

        prompt_path = Path(os.environ.get("SYSTEM_PROMPT_FILE", "app/prompts/system_prompt.txt"))
        raw_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        system_prompt = raw_prompt.replace("{{AGENT_NAME}}", agent_name)

        backend = os.environ.get("LLM_BACKEND", "ollama").strip().lower()
        if backend not in {"ollama", "cloud"}:
            raise RuntimeError(f"Invalid LLM_BACKEND: {backend!r} (use 'ollama' or 'cloud')")

        return cls(
            telegram_token=token,
            allowed_user_ids=_split_ids(os.environ.get("ALLOWED_USER_IDS", "")),
            agent_name=agent_name,
            system_prompt=system_prompt,
            timezone=os.environ.get("TZ", "UTC").strip() or "UTC",
            llm_backend=backend,
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            ollama_model=os.environ.get("OLLAMA_MODEL", "qwen3:8b"),
            cloud_api_base_url=os.environ.get("CLOUD_API_BASE_URL", "https://api.openai.com/v1"),
            cloud_api_key=os.environ.get("CLOUD_API_KEY", ""),
            cloud_model=os.environ.get("CLOUD_MODEL", "gpt-4o-mini"),
            whisper_model=os.environ.get("WHISPER_MODEL", "small"),
        )
