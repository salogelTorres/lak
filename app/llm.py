from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import httpx

from app.config import Config
from app.tools.base import Tool, ToolContext

logger = logging.getLogger(__name__)

# A chat message as sent to/received from the LLM. Kept as dict[str, Any]
# rather than dict[str, str]: an assistant message's "tool_calls" is a list,
# and its "content" can be None while a tool call is pending.
Message = dict[str, Any]
ToolCall = dict[str, Any]

# Bounded so a model that keeps requesting tools indefinitely can't loop
# forever — one final round always runs with tools withheld, forcing a
# plain-text answer. High enough that a search-then-read-a-few-pages research
# chain (search_web, then a couple of fetch_page calls) can actually finish.
MAX_TOOL_ROUNDS = 6


# Notified with a tool's name right before it runs, so the caller can let
# the user know something's happening (a tool call can take a few seconds —
# a web request, a file write — while the chat otherwise looks stalled).
OnToolCall = Callable[[str], Awaitable[None]]


class LLMClient(Protocol):
    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        context: ToolContext | None = None,
        on_tool_call: OnToolCall | None = None,
    ) -> str: ...  # pragma: no cover


# Sends one request and returns the raw assistant message dict. Implemented
# per backend (OllamaClient/CloudClient each shape their own payload), then
# driven by the shared _run_with_tools loop below. `think` only has an
# effect on backends/models that support extended reasoning (Ollama +
# e.g. qwen3) — CloudClient's closure just ignores it.
Complete = Callable[[list[Message], list[Tool] | None, bool], Awaitable[Message]]


async def _post_json(
    url: str, payload: dict[str, Any], *, headers: dict[str, str] | None, timeout: httpx.Timeout | float
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def _run_with_tools(
    complete: Complete,
    messages: list[Message],
    tools: list[Tool] | None,
    context: ToolContext | None = None,
    on_tool_call: OnToolCall | None = None,
) -> str:
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
        message = await complete(conversation, tools if offer_tools else None, False)
        calls: list[ToolCall] = message.get("tool_calls") or []
        if not calls:
            return message.get("content") or ""

        # Snapshot *before* this round's tool-call turn is appended, so a
        # tool that asks to "think harder" redoes the exact question that
        # led to it, not one already polluted by its own tool-call/result.
        round_context = _with_think_harder(context, complete, list(conversation))
        conversation.append({"role": "assistant", "content": message.get("content") or "", "tool_calls": calls})
        for call in calls:
            if on_tool_call:
                await on_tool_call(call.get("function", {}).get("name", ""))
            conversation.append(await _call_tool(tools_by_name, call, round_context))

    return "I tried using some tools but couldn't get to an answer. Could you rephrase?"


def _with_think_harder(
    context: ToolContext | None, complete: Complete, conversation_snapshot: list[Message]
) -> ToolContext | None:
    """Enrich `context` with a `think_harder` callback bound to this round's
    conversation, so app.tools.think_harder can redo it with extended
    reasoning on. Rebuilt every round since the conversation keeps growing.
    """
    if context is None:
        return None

    def think_harder() -> str:
        async def _ask() -> str:
            message = await complete(conversation_snapshot, None, True)
            return message.get("content") or ""

        return asyncio.run(_ask())

    return dataclasses.replace(context, think_harder=think_harder)


async def _call_tool(tools_by_name: dict[str, Tool], call: ToolCall, context: ToolContext | None = None) -> Message:
    function: dict[str, Any] = call.get("function", {})
    name: str = function.get("name", "")
    call_id: str = call.get("id", "")
    tool = tools_by_name.get(name)
    if tool is None:
        return {"role": "tool", "tool_call_id": call_id, "content": f"Unknown tool: {name}"}

    # Ollama's /api/chat hands back tool_calls[].function.arguments already
    # parsed into a dict; OpenAI-compatible /chat/completions sends it as a
    # JSON string. Handle both instead of assuming the OpenAI shape.
    raw_arguments = function.get("arguments") or {}
    if isinstance(raw_arguments, str):
        try:
            arguments: dict[str, Any] = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError:
            arguments = {}
    else:
        arguments = raw_arguments

    try:
        if tool.needs_context:
            result = await asyncio.to_thread(tool.execute, context=context, **arguments)
        else:
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

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        context: ToolContext | None = None,
        on_tool_call: OnToolCall | None = None,
    ) -> str:
        async def complete(msgs: list[Message], offered_tools: list[Tool] | None, think: bool = False) -> Message:
            payload: dict[str, Any] = {"model": self.model, "messages": msgs, "stream": False}
            if offered_tools:
                payload["tools"] = [tool.schema() for tool in offered_tools]
            if think:
                payload["think"] = True
            data = await _post_json(f"{self.base_url}/api/chat", payload, headers=None, timeout=self.TIMEOUT)
            return data["message"]

        return await _run_with_tools(complete, messages, tools, context, on_tool_call)


class CloudClient:
    """Talks to any OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        context: ToolContext | None = None,
        on_tool_call: OnToolCall | None = None,
    ) -> str:
        async def complete(msgs: list[Message], offered_tools: list[Tool] | None, think: bool = False) -> Message:
            # No standard OpenAI-compatible equivalent to Ollama's `think` —
            # think_harder still "works" here, it just re-asks plainly.
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

        return await _run_with_tools(complete, messages, tools, context, on_tool_call)


def build_llm_client(config: Config) -> LLMClient:
    if config.llm_backend == "ollama":
        return OllamaClient(config.ollama_base_url, config.ollama_model)
    return CloudClient(config.cloud_api_base_url, config.cloud_api_key, config.cloud_model)
