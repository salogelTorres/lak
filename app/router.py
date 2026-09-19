from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

THINK = "THINK"
NO_THINK = "NO_THINK"

# See evals/ROUTER_FINDINGS.md for how this was arrived at. Short version:
# think_harder (a tool the model self-invokes) never fired on real
# messages, even ones explicitly asking to "think carefully" — asking the
# model to classify the message first, as its own separate call, turned
# out to be a far more reliable signal than hoping it reaches for a tool.
# Nine alternative models were benchmarked against the same labeled,
# multilingual, adversarial-in-both-directions dataset
# (evals/router_dataset.py) before landing on this prompt/config; don't
# change this casually without re-running evals/router_bench.py against
# it, since a "small" wording tweak measurably moves accuracy there.
ROUTER_SYSTEM_PROMPT = (
    "You are a router in front of an AI assistant. Decide whether answering the user's "
    "message well requires careful step-by-step reasoning — multi-step math, logic, riddles "
    "or trick wording, planning under constraints, weighing trade-offs, debugging code — or "
    "whether it can be answered directly: greetings, simple facts, translations, rewrites, "
    "single-step arithmetic, or things that just need a tool such as weather, search, "
    "reminders or memory. The message may be in any language; judge the task, not the words "
    "used to ask it. Reply with exactly one word, THINK or NO_THINK, and nothing else.\n\n"
    "Examples:\n"
    "¿A qué hora abre el supermercado? -> NO_THINK\n"
    "Translate 'good night' into German. -> NO_THINK\n"
    "Wie spät ist es? -> NO_THINK\n"
    "Se una camicia costa 20 € dopo il 20% di sconto, quanto costava prima? -> THINK\n"
    "I have 3 meetings, 2 overlap, one is with my boss and I can only move one. Which, and why? -> THINK"
)

_THINK_TAGS_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# Ollama's structured-output support (a JSON schema passed as `format`)
# constrains the *next token* at the grammar level, forcing the model to
# emit the label directly instead of free-text it may or may not follow —
# some models otherwise launch into an open-ended, unstoppable ramble
# ("Okay, let's see...") no matter how many tokens they're given to
# eventually get there (see evals/ROUTER_FINDINGS.md, v1 vs v2).
_ROUTER_SCHEMA = {
    "type": "object",
    "properties": {"label": {"type": "string", "enum": [THINK, NO_THINK]}},
    "required": ["label"],
}


def parse_label(raw: str) -> str | None:
    """NO_THINK is checked first since "THINK" is a substring of it."""
    text = _THINK_TAGS_RE.sub("", raw).strip().upper()
    text = re.sub(r"[\s\-]+", "_", text)
    if "NO_THINK" in text or "NOTHINK" in text:
        return NO_THINK
    if "THINK" in text:
        return THINK
    return None


class OllamaRouter:
    """Decides, with a fast/cheap Ollama call, whether the current message
    needs extended reasoning (Ollama's `think: true`) — see
    evals/ROUTER_FINDINGS.md for why this is a dedicated classification
    call to a capable model rather than a smaller one, or a self-invoked
    tool. Ollama-only: there's no equivalent `think` flag to gate on any
    other backend, so app.bot only builds one when `Config.llm_backend`
    is `ollama` in the first place.
    """

    def __init__(self, base_url: str, model: str, *, temperature: float = 0.0, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    async def classify(self, text: str) -> bool:
        """True if `text` should get extended reasoning.

        Fails open (False) on any error, timeout, or unparseable response
        — a broken router must never block a reply, just skip the
        speed-up it would otherwise have bought.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "think": False,
            "format": _ROUTER_SCHEMA,
            # The schema still leaves room for `{"label": "...`, whitespace,
            # and closing punctuation around the enum value — a handful
            # more tokens than the bare word, but nowhere near what an
            # unconstrained model needs to ramble its way to an answer.
            "options": {"num_predict": 20, "temperature": self.temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
            raw = data.get("message", {}).get("content") or ""
        except Exception:
            logger.warning("Router call failed; skipping extended reasoning", exc_info=True)
            return False

        label = parse_label(raw)
        if label is None:
            logger.warning("Router returned an unparseable label %r; skipping extended reasoning", raw)
            return False
        return label == THINK
