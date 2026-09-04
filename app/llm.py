from __future__ import annotations

from typing import Protocol

import httpx

from app.config import Config

Message = dict[str, str]


class LLMClient(Protocol):
    async def chat(self, messages: list[Message]) -> str: ...  # pragma: no cover


class OllamaClient:
    # A cold model (nothing loaded into memory/VRAM yet, e.g. right after
    # `docker compose up`) can take a minute or more just to load before it
    # generates a single token, on top of generation time itself — a short
    # read timeout here fails that first request outright. Connect timeout
    # stays short so an unreachable Ollama still fails fast.
    TIMEOUT = httpx.Timeout(10.0, read=300.0)

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(self, messages: list[Message]) -> str:
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]


class CloudClient:
    """Talks to any OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[Message]) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


def build_llm_client(config: Config) -> LLMClient:
    if config.llm_backend == "ollama":
        return OllamaClient(config.ollama_base_url, config.ollama_model)
    return CloudClient(config.cloud_api_base_url, config.cloud_api_key, config.cloud_model)
