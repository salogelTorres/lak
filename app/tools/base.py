from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolContext:
    """Per-request context injected into tools that declare `needs_context`.

    This is *not* part of a tool's JSON schema — the model never sees or
    chooses `chat_id`, the caller (bot.py) supplies it. Keeps tools that
    need to know which chat they're running in (persistent memory,
    reminders) from having to be told by the model, which could be spoofed
    or simply wrong.
    """

    chat_id: int
    # schedule_reminder(delay_seconds, message): fire-and-forget a message
    # back to this chat after a delay. Owned by bot.py since that's where
    # the Telegram bot instance and the event loop live.
    schedule_reminder: Callable[[float, str], None]
    # think_harder(): re-runs the exact conversation that led to this tool
    # call, with the model's extended-reasoning mode turned on, and returns
    # its final answer. None when there's no conversation state to redo
    # (context built outside a tool-calling round). Owned by app.llm, since
    # only it has both the current conversation snapshot and the
    # backend-specific completion function — see app.llm._with_think_harder.
    think_harder: Callable[[], str] | None = None


@dataclass(frozen=True)
class Tool:
    """A capability an agent can opt into via ENABLED_TOOLS in .env.

    Tools are catalogued here independently of any given agent — an agent
    only gets one if its own config lists it by name (see
    app.tools.resolve_tools). `execute` is a plain, synchronous callable:
    the LLM client runs it via asyncio.to_thread, so it's free to block
    (e.g. on a network call) without freezing the event loop. When
    `needs_context` is set, it's called as `execute(context=..., **args)`
    instead of just `execute(**args)` — see app.llm._call_tool.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    execute: Callable[..., str]
    needs_context: bool = False

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
