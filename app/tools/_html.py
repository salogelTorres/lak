from __future__ import annotations

import html
import re

# Shared between web_search.py and fetch_page.py so both tools use the same
# rules for what counts as an injection attempt and how markup gets
# stripped — drifting these apart per tool would be easy to miss.

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_TAG_RE = re.compile(r"<[^>]+>")

# Fetched web content is untrusted and ends up straight in the model's
# context — redact anything that reads like an attempt to inject
# instructions rather than answer the query.
_INJECTION_PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(?:all\s+)?instructions\b", re.IGNORECASE),
    re.compile(r"\b(?:reveal|show|print)\s+(?:the\s+)?system\s+prompt\b", re.IGNORECASE),
)
REDACTED = "[external content omitted: looked like a prompt-injection attempt]"


def strip_markup(value: str) -> str:
    return _TAG_RE.sub("", html.unescape(value)).strip()


def normalize_url(value: str) -> str:
    if value and not value.startswith(("http://", "https://")):
        return f"https://{value}"
    return value


def looks_like_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)
