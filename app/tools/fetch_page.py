from __future__ import annotations

import logging
import re

import httpx

from app.tools._html import HEADERS, REDACTED, looks_like_injection, strip_markup
from app.tools.base import Tool

logger = logging.getLogger(__name__)

# Keeps one fetched page from dominating the model's context budget on its
# own — this is meant to complement search_web's snippets, not replace the
# whole conversation history.
MAX_CHARS = 4000

_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)


def fetch_page(url: str) -> str:
    """Fetch a URL and return its readable text for the model, truncated to
    a safe length.

    Errors — network failures, non-text content, pages that block automated
    requests — are never raised; they turn into a message telling the model
    the fetch didn't work, same philosophy as search_web.
    """
    url = url.strip()
    if not url:
        return "No URL was given."
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
            response = client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text" not in content_type:
                return f"Could not read {url}: not a text/HTML page (content-type: {content_type or 'unknown'})."
            page = response.text
    except httpx.HTTPError:
        logger.warning("Fetching %r failed", url, exc_info=True)
        return f"Could not fetch {url}. It may be down, blocking automated requests, or the URL may be wrong."

    text = strip_markup(_SCRIPT_STYLE_RE.sub("", page))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return f"Fetched {url} but found no readable text on the page."
    # The whole page is redacted rather than just the offending part: unlike
    # search_web's short snippets, there's no small unit here to cut out.
    if looks_like_injection(text):
        return REDACTED
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n...[truncated]"
    return text


TOOL = Tool(
    name="fetch_page",
    description=(
        "Fetch a specific web page and read its full text content. Use this after "
        "search_web when a result's snippet isn't enough and you need the actual "
        "article content. Always say where a fact came from when you use this."
    ),
    parameters={
        "type": "object",
        "required": ["url"],
        "properties": {
            "url": {"type": "string", "description": "The full URL of the page to read, from a search result."}
        },
    },
    execute=fetch_page,
)
