from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Tool:
    """A capability an agent can opt into via ENABLED_TOOLS in .env.

    Tools are catalogued here independently of any given agent — an agent
    only gets one if its own config lists it by name (see
    app.tools.resolve_tools). `execute` is a plain, synchronous callable:
    the LLM client runs it via asyncio.to_thread, so it's free to block
    (e.g. on a network call) without freezing the event loop.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    execute: Callable[..., str]

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
