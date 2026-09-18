"""Benchmark small models as a THINK / NO_THINK router, against a real Ollama.

The question this answers: before sending a message to the main model, can a
cheap, fast call decide reliably whether that message needs extended
reasoning (Ollama's `think: true`) or not — regardless of the user's
language? It does *not* run any thinking; it only measures the routing
decision itself, on the labeled cases in router_dataset.py.

For each candidate model it reports accuracy (per call and by majority vote
across attempts), the two error rates that matter for a router — missed
THINK cases (quality cost) and false THINK on easy ones (latency cost) —
consistency across attempts, per-language and per-category accuracy, and
latency. Raw per-call records go to a JSON file for later analysis.

Like evals/run.py this never runs under pytest. It only needs httpx and
Ollama reachable. From the host, against a Compose-published port:

    python -m evals.router_bench --base-url http://localhost:11434 \
        --models qwen3:0.6b qwen3:1.7b qwen3:4b qwen3:8b

Or inside the bot container, where the default base URL resolves:

    docker compose exec bot python -m evals.router_bench --models qwen3:8b

Models not yet pulled are reported and skipped, not treated as failures.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from evals.router_dataset import CASES, NO_THINK, THINK

# Short on purpose — it's re-sent on every call, so its length is most of the
# prompt-eval cost. Few-shot examples deliberately don't overlap the dataset.
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


def parse_label(raw: str) -> str | None:
    """Map a model's reply to THINK / NO_THINK, or None if it said neither.

    NO_THINK is checked first because "THINK" is a substring of it.
    """
    text = _THINK_TAGS_RE.sub("", raw).strip().upper()
    text = re.sub(r"[\s\-]+", "_", text)
    if "NO_THINK" in text or "NOTHINK" in text:
        return NO_THINK
    if "THINK" in text:
        return THINK
    return None


def majority(labels: list[str | None]) -> str | None:
    """Majority vote over attempts, ignoring unparseable ones; None on a tie."""
    votes = Counter(label for label in labels if label)
    if not votes:
        return None
    top = votes.most_common(2)
    if len(top) == 2 and top[0][1] == top[1][1]:
        return None
    return top[0][0]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(pct * (len(ordered) - 1))))]


def summarize(records: list[dict[str, Any]], cases: list[dict[str, str]]) -> dict[str, Any]:
    """Turn one model's per-call records into the numbers that matter for a router."""
    by_case: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_case[record["case"]].append(record)

    scored = [r for r in records if not r.get("error")]
    per_call_correct = sum(1 for r in scored if r["predicted"] == cases[r["case"]]["label"])

    votes = {idx: majority([r["predicted"] for r in rs]) for idx, rs in by_case.items()}
    consistent = sum(1 for rs in by_case.values() if len({r["predicted"] for r in rs}) == 1)

    tp = fn = fp = tn = 0
    per_lang: dict[str, list[bool]] = defaultdict(list)
    per_category: dict[str, list[bool]] = defaultdict(list)
    misclassified = []
    for idx, predicted in votes.items():
        case = cases[idx]
        correct = predicted == case["label"]
        per_lang[case["lang"]].append(correct)
        per_category[case["category"]].append(correct)
        if case["label"] == THINK:
            tp += correct
            fn += not correct
        else:
            tn += correct
            fp += not correct
        if not correct:
            misclassified.append(
                {
                    "text": case["text"],
                    "label": case["label"],
                    "majority": predicted,
                    "raw": [r["raw"] for r in by_case[idx]],
                }
            )

    wall = [r["wall_ms"] for r in scored]
    prompt_eval = [r["prompt_eval_ms"] for r in scored if r.get("prompt_eval_ms") is not None]
    eval_ms = [r["eval_ms"] for r in scored if r.get("eval_ms") is not None]

    def ratio(num: int, den: int) -> float | None:
        return num / den if den else None

    return {
        "cases": len(by_case),
        "calls": len(records),
        "errors": len(records) - len(scored),
        "unparseable_calls": sum(1 for r in scored if r["predicted"] is None),
        "ties": sum(1 for idx, rs in by_case.items() if votes[idx] is None and any(r["predicted"] for r in rs)),
        "per_call_accuracy": ratio(per_call_correct, len(scored)),
        "majority_accuracy": ratio(tp + tn, len(votes)),
        "consistency": ratio(consistent, len(by_case)),
        "think_recall": ratio(tp, tp + fn),  # 1 - missed-THINK rate (quality cost)
        "no_think_recall": ratio(tn, tn + fp),  # 1 - false-THINK rate (latency cost)
        "think_precision": ratio(tp, tp + fp),
        "confusion": {"tp": tp, "fn": fn, "fp": fp, "tn": tn},
        "per_lang_accuracy": {lang: sum(v) / len(v) for lang, v in sorted(per_lang.items())},
        "per_category_accuracy": {cat: sum(v) / len(v) for cat, v in sorted(per_category.items())},
        "latency_ms": {
            "median": statistics.median(wall) if wall else None,
            "mean": statistics.fmean(wall) if wall else None,
            "p95": _percentile(wall, 0.95) if wall else None,
            "prompt_eval_median": statistics.median(prompt_eval) if prompt_eval else None,
            "eval_median": statistics.median(eval_ms) if eval_ms else None,
        },
        "misclassified": misclassified,
    }


def baseline_accuracy(cases: list[dict[str, str]]) -> float:
    """Accuracy of always answering the majority class — the bar to clear."""
    counts = Counter(case["label"] for case in cases)
    return counts.most_common(1)[0][1] / len(cases)


async def _available_models(client: httpx.AsyncClient, base_url: str) -> set[str]:
    response = await client.get(f"{base_url}/api/tags")
    response.raise_for_status()
    names = set()
    for model in response.json().get("models", []):
        name = model.get("name", "")
        names.add(name)
        if name.endswith(":latest"):
            names.add(name[: -len(":latest")])
    return names


async def _supports_thinking(client: httpx.AsyncClient, base_url: str, model: str) -> bool:
    response = await client.post(f"{base_url}/api/show", json={"model": model})
    response.raise_for_status()
    return "thinking" in response.json().get("capabilities", [])


async def _classify(
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
    text: str,
    *,
    disable_thinking: bool,
    temperature: float | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "stream": False,
        # A handful of tokens is all a one-word answer needs; anything past
        # that is the model rambling, and with generation being the slow
        # part on modest hardware, capping it is what keeps a router cheap.
        "options": {"num_predict": 5},
    }
    if disable_thinking:
        payload["think"] = False
    if temperature is not None:
        payload["options"]["temperature"] = temperature

    started = time.perf_counter()
    try:
        response = await client.post(f"{base_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        return {"raw": "", "predicted": None, "wall_ms": (time.perf_counter() - started) * 1000, "error": str(exc)}
    raw = data.get("message", {}).get("content") or ""
    return {
        "raw": raw,
        "predicted": parse_label(raw),
        "wall_ms": (time.perf_counter() - started) * 1000,
        "prompt_eval_ms": (data.get("prompt_eval_duration") or 0) / 1e6,
        "eval_ms": (data.get("eval_duration") or 0) / 1e6,
        "load_ms": (data.get("load_duration") or 0) / 1e6,
        "eval_count": data.get("eval_count"),
    }


async def bench_model(
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
    cases: list[dict[str, str]],
    *,
    attempts: int,
    temperature: float | None,
) -> tuple[list[dict[str, Any]], float]:
    disable_thinking = await _supports_thinking(client, base_url, model)
    # One unrecorded call first, so the cold model load doesn't land in the
    # latency stats of whichever case happens to run first.
    warm = await _classify(
        client, base_url, model, "Hola", disable_thinking=disable_thinking, temperature=temperature
    )
    load_ms = warm.get("load_ms") or 0.0

    records = []
    total = len(cases) * attempts
    for idx, case in enumerate(cases):
        for attempt in range(attempts):
            result = await _classify(
                client, base_url, model, case["text"], disable_thinking=disable_thinking, temperature=temperature
            )
            records.append({"model": model, "case": idx, "attempt": attempt, **result})
            done = idx * attempts + attempt + 1
            print(f"\r  {model}: {done}/{total}", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)
    return records, load_ms


def _fmt_pct(value: float | None) -> str:
    return "  n/a" if value is None else f"{value * 100:5.1f}%"


def _fmt_ms(value: float | None) -> str:
    return "   n/a" if value is None else f"{value:6.0f}"


def print_report(summaries: dict[str, dict[str, Any]], load_ms: dict[str, float], cases: list[dict[str, str]]) -> None:
    print(f"\nCases: {len(cases)}   always-{Counter(c['label'] for c in cases).most_common(1)[0][0]} "
          f"baseline: {baseline_accuracy(cases) * 100:.1f}%\n")
    header = (
        f"{'model':<14} {'maj acc':>8} {'call acc':>9} {'THINK rec':>10} {'NO_THINK rec':>13} "
        f"{'consist':>8} {'unparsed':>9} {'med ms':>7} {'p95 ms':>7} {'load ms':>8}"
    )
    print(header)
    print("-" * len(header))
    for model, s in summaries.items():
        lat = s["latency_ms"]
        print(
            f"{model:<14} {_fmt_pct(s['majority_accuracy']):>8} {_fmt_pct(s['per_call_accuracy']):>9} "
            f"{_fmt_pct(s['think_recall']):>10} {_fmt_pct(s['no_think_recall']):>13} "
            f"{_fmt_pct(s['consistency']):>8} {s['unparseable_calls']:>9} "
            f"{_fmt_ms(lat['median']):>7} {_fmt_ms(lat['p95']):>7} {_fmt_ms(load_ms.get(model)):>8}"
        )

    for model, s in summaries.items():
        print(f"\n== {model} ==")
        print("  by language: " + "  ".join(f"{k} {v * 100:.0f}%" for k, v in s["per_lang_accuracy"].items()))
        print("  by category:")
        for category, acc in s["per_category_accuracy"].items():
            print(f"    {category:<20} {acc * 100:5.1f}%")
        if s["errors"]:
            print(f"  errors: {s['errors']} call(s) failed (see JSON)")
        if s["misclassified"]:
            print(f"  misclassified ({len(s['misclassified'])}):")
            for item in s["misclassified"]:
                text = item["text"].replace("\n", " ")
                text = text if len(text) <= 90 else text[:87] + "..."
                print(f"    [{item['label']:<8} -> {str(item['majority']):<8}] {text}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="+", required=True, help="Ollama model names to compare")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434"),
        help="Ollama base URL (default: $OLLAMA_BASE_URL or http://ollama:11434)",
    )
    parser.add_argument("--attempts", type=int, default=3, help="calls per case, for majority vote + consistency")
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="sampling temperature (default: the model's own; use 0 to test the deterministic config)",
    )
    parser.add_argument("--limit", type=int, default=None, help="only run the first N cases (quick smoke test)")
    parser.add_argument("--timeout", type=float, default=120.0, help="per-call timeout in seconds")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="where to write raw results as JSON (default: evals/results/router_bench_<timestamp>.json)",
    )
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cases = CASES[: args.limit] if args.limit else CASES
    base_url = args.base_url.rstrip("/")
    out = args.out or Path("evals") / "results" / f"router_bench_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"

    summaries: dict[str, dict[str, Any]] = {}
    load_ms: dict[str, float] = {}
    all_records: dict[str, list[dict[str, Any]]] = {}

    async with httpx.AsyncClient(timeout=args.timeout) as client:
        try:
            available = await _available_models(client, base_url)
        except httpx.HTTPError as exc:
            print(f"Can't reach Ollama at {base_url}: {exc}", file=sys.stderr)
            return 2

        for model in args.models:
            if model not in available:
                print(f"skipping {model}: not pulled (docker compose exec ollama ollama pull {model})", file=sys.stderr)
                continue
            records, load_ms[model] = await bench_model(
                client, base_url, model, cases, attempts=args.attempts, temperature=args.temperature
            )
            all_records[model] = records
            summaries[model] = summarize(records, cases)

    if not summaries:
        print("Nothing benchmarked.", file=sys.stderr)
        return 1

    print_report(summaries, load_ms, cases)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "meta": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "base_url": base_url,
                    "attempts": args.attempts,
                    "temperature": args.temperature,
                    "cases": len(cases),
                    "router_system_prompt": ROUTER_SYSTEM_PROMPT,
                },
                "models": {
                    model: {"summary": summaries[model], "load_ms": load_ms[model], "records": all_records[model]}
                    for model in summaries
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nRaw results: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
