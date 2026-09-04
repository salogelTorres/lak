from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import httpx

from app.config import Config
from app.tools.base import Tool

logger = logging.getLogger(__name__)

# A chat message as sent to/received from the LLM. Kept as dict[str, Any]
# rather than dict[str, str]: an assistant message's "tool_calls" is a list,
# and its "content" can be None while a tool call is pending.
Message = dict[str, Any]
ToolCall = dict[str, Any]

# Bounded so a model that keeps requesting tools indefinitely can't loop
# forever — one final round always runs with tools withheld, forcing a
# plain-text answer.
MAX_TOOL_ROUNDS = 3


class LLMClient(Protocol):
    async def chat(self, messages: list[Message], tools: list[Tool] | None = None) -> str: ...  # pragma: no cover


# Sends one request and returns the raw assistant message dict. Implemented
# per backend (OllamaClient/CloudClient each shape their own payload), then
# driven by the shared _run_with_tools loop below.
Complete = Callable[[list[Message], list[Tool] | None], Awaitable[Message]]


async def _post_json(
    url: str, payload: dict[str, Any], *, headers: dict[str, str] | None, timeout: httpx.Timeout | float
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def _run_with_tools(complete: Complete, messages: list[Message], tools: list[Tool] | None) -> str:
    """Drive an OpenAI-style tool-calling loop shared by both backends.

    `complete` sends one request and returns the raw assistant message dict
    (`content`, and optionally `tool_calls`) — Ollama's /api/chat and any
    OpenAI-compatible /chat/completions endpoint both speak this same
    tool-calling shape, so one loop covers both.
    """
    if not tools:
        message = await complete(messages, None)
        return message.get("content") or ""

    tools_by_name = {tool.name: tool for tool in tools}
    conversation = list(messages)
    for round_index in range(MAX_TOOL_ROUNDS + 1):
        offer_tools = round_index < MAX_TOOL_ROUNDS
        message = await complete(conversation, tools if offer_tools else None)
        calls: list[ToolCall] = message.get("tool_calls") or []
        if not calls:
            return message.get("content") or ""

        conversation.append({"role": "assistant", "content": message.get("content") or "", "tool_calls": calls})
        for call in calls:
            conversation.append(await _call_tool(tools_by_name, call))

    return "I tried using some tools but couldn't get to an answer. Could you rephrase?"


async def _call_tool(tools_by_name: dict[str, Tool], call: ToolCall) -> Message:
    function: dict[str, Any] = call.get("function", {})
    name: str = function.get("name", "")
    call_id: str = call.get("id", "")
    tool = tools_by_name.get(name)
    if tool is None:
        return {"role": "tool", "tool_call_id": call_id, "content": f"Unknown tool: {name}"}

    try:
        arguments: dict[str, Any] = json.loads(function.get("arguments") or "{}")
    except json.JSONDecodeError:
        arguments = {}

    try:
        result = await asyncio.to_thread(tool.execute, **arguments)
    except Exception:
        logger.exception("Tool %r failed", name)
        result = f"The {name} tool failed to run."

    return {"role": "tool", "tool_call_id": call_id, "content": str(result)}


class OllamaClient:
    # A cold model (nothing loaded into memory/VRAM yet, e.g. right after
    # `docker compose up`) can take a minute or more just to load before it
    # generates a single token, on top of generation time itself — a short
    # read timeout here fails that first request outright. Connect timeout
    # stays short so an unreachable Ollama still fails fast.
    TIMEOUT = httpx.Timeout(10.0, read=300.0)

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(self, messages: list[Message], tools: list[Tool] | None = None) -> str:
        async def complete(msgs: list[Message], offered_tools: list[Tool] | None) -> Message:
            payload: dict[str, Any] = {"model": self.model, "messages": msgs, "stream": False}
            if offered_tools:
                payload["tools"] = [tool.schema() for tool in offered_tools]
            data = await _post_json(f"{self.base_url}/api/chat", payload, headers=None, timeout=self.TIMEOUT)
            return data["message"]

        return await _run_with_tools(complete, messages, tools)


class CloudClient:
    """Talks to any OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[Message], tools: list[Tool] | None = None) -> str:
        async def complete(msgs: list[Message], offered_tools: list[Tool] | None) -> Message:
            payload: dict[str, Any] = {"model": self.model, "messages": msgs}
            if offered_tools:
                payload["tools"] = [tool.schema() for tool in offered_tools]
                payload["tool_choice"] = "auto"
            data = await _post_json(
                f"{self.base_url}/chat/completions",
                payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120,
            )
            return data["choices"][0]["message"]

        return await _run_with_tools(complete, messages, tools)


def build_llm_client(config: Config) -> LLMClient:
    if config.llm_backend == "ollama":
        return OllamaClient(config.ollama_base_url, config.ollama_model)
    return CloudClient(config.cloud_api_base_url, config.cloud_api_key, config.cloud_model)
