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
import sys
from collections.abc import Callable
from dataclasses import dataclass

import app.llm as llm_module
from app.config import Config
from app.tools import resolve_tools


@dataclass(frozen=True)
class EvalCase:
    name: str
    system_prompt: str
    user_message: str
    # judge(reply, tool_names_called_in_order) -> (passed, reason)
    judge: Callable[[str, list[str]], tuple[bool, str]]


def used_tool(name: str) -> Callable[[str, list[str]], tuple[bool, str]]:
    def judge(reply: str, tools_called: list[str]) -> tuple[bool, str]:
        if name in tools_called:
            return True, f"called {name!r} as expected"
        return False, f"expected a call to {name!r}, got {tools_called or 'no tool calls'}"

    return judge


def used_no_tools() -> Callable[[str, list[str]], tuple[bool, str]]:
    def judge(reply: str, tools_called: list[str]) -> tuple[bool, str]:
        if not tools_called:
            return True, "used no tools, as expected"
        return False, f"expected no tool calls, got {tools_called}"

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
    original_call_tool = llm_module._call_tool

    async def spying_call_tool(tools_by_name, call):
        tools_called.append(call.get("function", {}).get("name", ""))
        return await original_call_tool(tools_by_name, call)

    llm_module._call_tool = spying_call_tool
    try:
        client = llm_module.build_llm_client(config)
        tools = resolve_tools(config.enabled_tools)
        messages = [
            {"role": "system", "content": case.system_prompt},
            {"role": "user", "content": case.user_message},
        ]
        reply = await client.chat(messages, tools=tools)
    finally:
        llm_module._call_tool = original_call_tool

    return case.judge(reply, tools_called)


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

    print(f"\n{len(CASES) - failures}/{len(CASES)} passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
