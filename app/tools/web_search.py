from __future__ import annotations

import logging
import re

import httpx

from app.tools._html import HEADERS, REDACTED, looks_like_injection, normalize_url, strip_markup
from app.tools.base import Tool

logger = logging.getLogger(__name__)

DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
MAX_RESULTS = 5

# One pattern per result: the URL comes from the *same* anchor as the title,
# and the snippet is looked up within the chunk running up to the next
# result. Matching title/snippet/URL independently and pairing them by index
# breaks as soon as one result is missing a piece — ads don't carry the
# usual result__url, which shifts every later result by one.
_RESULT_RE = re.compile(
    r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>(.*?)(?=class="result__a"|\Z)', re.DOTALL
)
_SNIPPET_RE = re.compile(r'class="result__snippet"[^>]*>(.*?)</(?:a|span)>', re.DOTALL)
# Ads point at DuckDuckGo's own redirector instead of the actual site —
# drop them, since citing one as a source would misattribute it to
# DuckDuckGo rather than whoever is actually saying it.
_AD_MARKER = "duckduckgo.com/y.js"


def _fetch_search_page(query: str) -> str:
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
            response = client.post(DUCKDUCKGO_HTML_URL, data={"q": query})
            response.raise_for_status()
            return response.text
    except httpx.HTTPError:
        logger.warning("DuckDuckGo request failed", exc_info=True)
        return ""


def _extract_results(page: str, max_results: int) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for href, raw_title, chunk in _RESULT_RE.findall(page):
        title = strip_markup(raw_title)
        if not title or _AD_MARKER in href:
            continue
        snippet_match = _SNIPPET_RE.search(chunk)
        snippet = strip_markup(snippet_match.group(1)) if snippet_match else ""
        if looks_like_injection(title) or looks_like_injection(snippet):
            title, snippet = REDACTED, ""
        results.append({"title": title, "href": normalize_url(strip_markup(href)), "snippet": snippet})
        if len(results) == max_results:
            break
    return results


def search_web(query: str, max_results: int = MAX_RESULTS) -> str:
    """Search DuckDuckGo (no API key) and return the results as plain text
    for the model to read.

    Errors — network failures, no results, DuckDuckGo blocking the request —
    are never raised; they turn into a message telling the model the search
    didn't work, so a broken search never crashes the conversation and the
    model doesn't confidently claim something doesn't exist just because the
    search itself failed.
    """
    query = query.strip()
    if not query:
        return "No search query was given."

    page = _fetch_search_page(query)
    results = _extract_results(page, max_results) if page else []
    if not results:
        return (
            "The search returned no results. This could mean nothing relevant "
            "exists, or that the search itself failed — say so, don't claim "
            "something doesn't exist."
        )
    return "\n\n".join(f"{r['title']}\n{r['href']}\n{r['snippet']}" for r in results)


TOOL = Tool(
    name="search_web",
    description=(
        "Search the web. Use it for facts you're not confident about, current "
        "events, or anything that could have changed since your training data. "
        "Always say where a fact came from when you use this."
    ),
    parameters={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "The search terms, not the whole question."}
        },
    },
    execute=search_web,
)
