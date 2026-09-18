"""Manual eval suite for tool-use behavior against a real LLM.

Unlike `tests/` (100% mocked, deterministic, gated at 99% coverage), these
evals call the actual configured backend and judge the model's own choices —
slow, not fully deterministic, and not something CI should block on. They
never run as part of `pytest`.

Requires a working .env (same one the bot itself uses) with at least one
tool enabled, and the backend it points at actually reachable from wherever
this runs. For the `ollama` backend that usually means running this inside
the bot container, where OLLAMA_BASE_URL's default (http://ollama:11434)
resolves over the Compose network:

    docker compose exec bot python -m evals.run

Running it on the host instead works too, as long as OLLAMA_BASE_URL in
.env points somewhere reachable from the host (e.g. http://localhost:11434
if Ollama's port is published).
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import app.llm as llm_module
import app.tools.memory as memory_module
from app.config import Config
from app.tools import resolve_tools
from app.tools.base import ToolContext

# A fixed, isolated chat id/memory file for the duration of a run, so evals
# never read or write the real agent's remembered notes and are repeatable
# from a clean slate every time.
EVAL_CHAT_ID = -1


@dataclass(frozen=True)
class EvalCase:
    name: str
    system_prompt: str
    user_message: str
    # judge(reply, tool_names_called_in_order, recorded_reminders) -> (passed, reason)
    judge: Callable[[str, list[str], list[tuple[float, str]]], tuple[bool, str]]


def used_tool(name: str) -> Callable[[str, list[str], list], tuple[bool, str]]:
    def judge(reply: str, tools_called: list[str], _reminders: list) -> tuple[bool, str]:
        if name in tools_called:
            return True, f"called {name!r} as expected"
        return False, f"expected a call to {name!r}, got {tools_called or 'no tool calls'}"

    return judge


def used_no_tools() -> Callable[[str, list[str], list], tuple[bool, str]]:
    def judge(reply: str, tools_called: list[str], _reminders: list) -> tuple[bool, str]:
        if not tools_called:
            return True, "used no tools, as expected"
        return False, f"expected no tool calls, got {tools_called}"

    return judge


def used_weather_and_mentioned_a_temperature() -> Callable[[str, list[str], list], tuple[bool, str]]:
    """Stronger than used_tool: also checks the reply actually surfaces a
    temperature reading rather than the tool call succeeding but the model
    ignoring its result."""

    def judge(reply: str, tools_called: list[str], _reminders: list) -> tuple[bool, str]:
        if "get_weather" not in tools_called:
            return False, f"expected a call to 'get_weather', got {tools_called or 'no tool calls'}"
        if "°" not in reply and "degrees" not in reply.lower():
            return False, f"called get_weather but reply doesn't mention a temperature: {reply!r}"
        return True, "called get_weather and reported a temperature"

    return judge


def scheduled_a_reminder() -> Callable[[str, list[str], list[tuple[float, str]]], tuple[bool, str]]:
    """Stronger than used_tool: checks remind_me was actually invoked with a
    sane (positive, non-trivial) delay, not just that the model called it."""

    def judge(reply: str, tools_called: list[str], reminders: list[tuple[float, str]]) -> tuple[bool, str]:
        if "remind_me" not in tools_called:
            return False, f"expected a call to 'remind_me', got {tools_called or 'no tool calls'}"
        if not reminders:
            return False, "remind_me was called but scheduled nothing (execution likely failed)"
        delay_seconds, message = reminders[-1]
        if delay_seconds <= 0:
            return False, f"scheduled a non-positive delay: {delay_seconds}"
        if not message.strip():
            return False, "scheduled a reminder with an empty message"
        return True, f"scheduled a reminder in {delay_seconds:g}s: {message!r}"

    return judge


CASES = [
    EvalCase(
        name="uses search_web for a current-events question",
        system_prompt="You are a helpful assistant.",
        user_message="What's the latest news about AI regulation this week?",
        judge=used_tool("search_web"),
    ),
    EvalCase(
        name="uses fetch_page to read a full article after searching",
        system_prompt=(
            "You are a helpful assistant. When search_web's snippets aren't enough "
            "to answer in detail, use fetch_page to read the full article."
        ),
        user_message=(
            "Search for recent AI news and give me a detailed summary of one "
            "specific article, reading the full page rather than just the snippet."
        ),
        judge=used_tool("fetch_page"),
    ),
    EvalCase(
        name="uses get_weather and reports an actual temperature",
        system_prompt="You are a helpful assistant.",
        user_message="What's the weather like in Madrid right now?",
        judge=used_weather_and_mentioned_a_temperature(),
    ),
    EvalCase(
        name="uses remind_me with a sane delay when asked to be reminded",
        system_prompt="You are a helpful assistant.",
        user_message="Remind me to call my dentist in 20 minutes.",
        judge=scheduled_a_reminder(),
    ),
    EvalCase(
        name="does not reach for tools on basic chit-chat",
        system_prompt="You are a helpful assistant.",
        user_message="Hi! How are you today?",
        judge=used_no_tools(),
    ),
    EvalCase(
        name="does not reach for tools on stable general knowledge",
        system_prompt="You are a helpful assistant.",
        user_message="What is the capital of France?",
        judge=used_no_tools(),
    ),
]


async def _run_case(case: EvalCase, config: Config) -> tuple[bool, str]:
    tools_called: list[str] = []
    reminders: list[tuple[float, str]] = []
    original_call_tool = llm_module._call_tool

    async def spying_call_tool(tools_by_name, call, context=None):
        tools_called.append(call.get("function", {}).get("name", ""))
        return await original_call_tool(tools_by_name, call, context)

    llm_module._call_tool = spying_call_tool
    try:
        client = llm_module.build_llm_client(config)
        tools = resolve_tools(config.enabled_tools)
        context = ToolContext(
            chat_id=EVAL_CHAT_ID, schedule_reminder=lambda delay, message: reminders.append((delay, message))
        )
        messages = [
            {"role": "system", "content": case.system_prompt},
            {"role": "user", "content": case.user_message},
        ]
        reply = await client.chat(messages, tools=tools, context=context)
    finally:
        llm_module._call_tool = original_call_tool

    return case.judge(reply, tools_called, reminders)


async def _run_memory_round_trip(config: Config, memory_file: Path) -> tuple[bool, str]:
    """Strong eval for remember/recall: unlike the single-turn cases above,
    this actually checks persistence — that a fact saved in one exchange
    comes back correctly in a *separate* one, via the real memory file on
    disk, not just that the model chose to call the right tool name.
    """
    memory_module.MEMORY_FILE = memory_file
    tools = resolve_tools(config.enabled_tools)
    context = ToolContext(chat_id=EVAL_CHAT_ID, schedule_reminder=lambda *_: None)
    client = llm_module.build_llm_client(config)

    remember_prompt = [
        {"role": "system", "content": "You are a helpful assistant. Use remember to save durable facts the user shares."},
        {"role": "user", "content": "Please remember that my favorite color is turquoise."},
    ]
    await client.chat(remember_prompt, tools=tools, context=context)

    if str(EVAL_CHAT_ID) not in _load_chat_ids(memory_file):
        return False, "remember didn't persist anything to the memory file"

    recall_prompt = [
        {"role": "system", "content": "You are a helpful assistant. Use recall to check what you remember about the user."},
        {"role": "user", "content": "What do you remember about my favorite color?"},
    ]
    reply = await client.chat(recall_prompt, tools=tools, context=context)

    if "turquoise" not in reply.lower():
        return False, f"recall didn't surface the remembered fact in the reply: {reply!r}"
    return True, "remembered fact persisted and was correctly recalled in a separate exchange"


def _load_chat_ids(memory_file: Path) -> list[str]:
    try:
        return list(json.loads(memory_file.read_text(encoding="utf-8")).keys())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


async def main() -> int:
    config = Config.load()
    if not config.enabled_tools:
        print("ENABLED_TOOLS is empty in .env — nothing to evaluate.")
        print("Set it to something like search_web,fetch_page and try again.")
        return 1

    failures = 0
    for case in CASES:
        passed, reason = await _run_case(case, config)
        print(f"[{'PASS' if passed else 'FAIL'}] {case.name}: {reason}")
        failures += 0 if passed else 1

    total = len(CASES)
    if {"remember", "recall"} <= set(config.enabled_tools):
        total += 1
        with tempfile.TemporaryDirectory() as tmp_dir:
            passed, reason = await _run_memory_round_trip(config, Path(tmp_dir) / "eval_memory.json")
            print(f"[{'PASS' if passed else 'FAIL'}] remember/recall round-trips across a separate exchange: {reason}")
            failures += 0 if passed else 1

    print(f"\n{total - failures}/{total} passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
