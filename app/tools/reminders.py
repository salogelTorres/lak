from __future__ import annotations

from app.tools.base import Tool, ToolContext

# A sanity ceiling, not a real product limit — keeps a misfired "remind me
# in 999999 minutes" from silently scheduling something absurd instead of
# telling the model to reconsider.
MAX_MINUTES = 60 * 24 * 7  # one week


def remind_me(minutes: float, message: str, *, context: ToolContext) -> str:
    """Schedule `message` to be sent back to this chat after `minutes`.

    Delivery itself (actually sending the message later) is bot.py's job —
    this tool only validates the request and hands it to
    context.schedule_reminder, which bot.py wires up per chat.
    """
    message = message.strip()
    if not message:
        return "No reminder message was given."
    if minutes <= 0:
        return "The reminder time must be a positive number of minutes from now."
    if minutes > MAX_MINUTES:
        return f"That's too far out — pick something under {MAX_MINUTES} minutes from now."

    context.schedule_reminder(minutes * 60, message)
    return f"Reminder set for {minutes:g} minute(s) from now: {message!r}"


TOOL = Tool(
    name="remind_me",
    description=(
        "Schedule a reminder to be sent back to this chat after a delay. Use it when the "
        "user asks to be reminded of something later."
    ),
    parameters={
        "type": "object",
        "required": ["minutes", "message"],
        "properties": {
            "minutes": {"type": "number", "description": "How many minutes from now to send the reminder."},
            "message": {"type": "string", "description": "What to remind the user about."},
        },
    },
    execute=remind_me,
    needs_context=True,
)
