from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

from app.tools.base import Tool, ToolContext

logger = logging.getLogger(__name__)

# A Docker volume mounts here (see docker-compose.yml's memory_data), so
# notes survive `docker compose down`/`up` — same pattern as
# WHISPER_DOWNLOAD_ROOT in bot.py. Overridable for tests.
MEMORY_FILE = Path(os.environ.get("MEMORY_FILE", "/data/memory/memory.json"))

# A ceiling, not a target: keeps one chat's notes from growing without bound
# rather than trying to be a real database.
MAX_NOTES_PER_CHAT = 200

# Tool execution runs in a thread pool (see app.llm._call_tool's
# asyncio.to_thread) — concurrent remember() calls for different chats could
# race on this single JSON file's read-modify-write otherwise.
_lock = threading.Lock()


def _load() -> dict[str, list[str]]:
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.warning("Memory file was corrupt; starting fresh", exc_info=True)
        return {}


def _save(data: dict[str, list[str]]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(data), encoding="utf-8")


def remember(note: str, *, context: ToolContext) -> str:
    note = note.strip()
    if not note:
        return "No note was given to remember."

    with _lock:
        data = _load()
        notes = data.setdefault(str(context.chat_id), [])
        notes.append(note)
        del notes[:-MAX_NOTES_PER_CHAT]
        _save(data)

    return f"Remembered: {note!r}"


def recall(*, context: ToolContext) -> str:
    with _lock:
        data = _load()

    notes = data.get(str(context.chat_id), [])
    if not notes:
        return "Nothing has been remembered yet for this chat."
    return "\n".join(f"- {note}" for note in notes)


REMEMBER_TOOL = Tool(
    name="remember",
    description=(
        "Save a short note or fact to persistent memory for this chat, so it survives "
        "restarts. Use it when the user asks you to remember something, or shares a "
        "durable preference/fact worth keeping for later."
    ),
    parameters={
        "type": "object",
        "required": ["note"],
        "properties": {
            "note": {"type": "string", "description": "The fact or note to remember, written plainly."}
        },
    },
    execute=remember,
    needs_context=True,
)

RECALL_TOOL = Tool(
    name="recall",
    description=(
        "Retrieve everything remembered so far for this chat. Use it when the user asks "
        "what you remember, or when a previously saved note might be relevant."
    ),
    parameters={"type": "object", "properties": {}},
    execute=recall,
    needs_context=True,
)
