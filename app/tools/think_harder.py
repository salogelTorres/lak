from __future__ import annotations

from app.tools.base import Tool, ToolContext

# Prepended so the outer (non-thinking) model relays this verbatim instead
# of rephrasing or second-guessing an answer that already got the careful
# pass — the whole point of calling this tool is to *not* redo that work.
_PREFIX = (
    "[This answer was produced with extended reasoning enabled. Relay it to "
    "the user as-is — don't shorten, rephrase, or second-guess it.]\n\n"
)


def think_harder(*, context: ToolContext) -> str:
    """Re-run the current question with the model's extended-reasoning mode
    turned on, via context.think_harder (owned by app.llm — see
    _with_think_harder). Only has a real effect on backends/models that
    support it (Ollama + e.g. qwen3); elsewhere it degrades to a plain
    re-ask, which still can't hurt.
    """
    if context.think_harder is None:
        return "Extended reasoning isn't available right now — answer normally instead."

    answer = context.think_harder().strip()
    if not answer:
        return "Thinking harder didn't produce a usable answer — answer normally instead."
    return f"{_PREFIX}{answer}"


TOOL = Tool(
    name="think_harder",
    description=(
        "Re-answer the user's current question with extended reasoning enabled. Use it "
        "for questions that need careful multi-step thinking — tricky math, logic "
        "puzzles, planning, anything you're not confident about after a normal pass — "
        "instead of guessing."
    ),
    parameters={"type": "object", "properties": {}},
    execute=think_harder,
    needs_context=True,
)
