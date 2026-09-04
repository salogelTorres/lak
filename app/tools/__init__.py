from __future__ import annotations

from app.tools.base import Tool
from app.tools.web_search import TOOL as _web_search

# The catalog of every tool this template ships with. An agent doesn't get
# any of these by default — it opts in per tool via ENABLED_TOOLS in .env,
# resolved through resolve_tools() below. Add new tools here.
AVAILABLE_TOOLS: dict[str, Tool] = {tool.name: tool for tool in (_web_search,)}


def resolve_tools(names: list[str]) -> list[Tool]:
    """Look up enabled tool names against the catalog, silently skipping
    unknown ones (e.g. a name left over from a tool the template later
    renamed or removed)."""
    return [AVAILABLE_TOOLS[name] for name in names if name in AVAILABLE_TOOLS]
