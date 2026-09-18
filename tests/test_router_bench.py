"""Unit tests for the router benchmark's pure parts (label parsing, voting,
metrics) and sanity checks on the labeled dataset. The benchmark itself
talks to a real Ollama and is never run under pytest; these guard the bits
that would silently corrupt its numbers if wrong."""
from collections import Counter

import pytest

from evals.router_bench import ROUTER_SYSTEM_PROMPT, baseline_accuracy, majority, parse_label, summarize
from evals.router_dataset import CASES, NO_THINK, THINK


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("THINK", THINK),
        ("NO_THINK", NO_THINK),
        ("no_think", NO_THINK),
        ("No think", NO_THINK),
        ("NO-THINK.", NO_THINK),
        ("  THINK\n", THINK),
        ("Answer: THINK", THINK),
        ("<think>hmm</think>NO_THINK", NO_THINK),
        ("I don't know", None),
        ("", None),
    ],
)
def test_parse_label(raw, expected):
    assert parse_label(raw) == expected


def test_parse_label_does_not_mistake_no_think_for_think():
    # "THINK" is a substring of "NO_THINK" — order of checks matters.
    assert parse_label("NO_THINK") == NO_THINK
    assert parse_label("NOTHINK") == NO_THINK


def test_majority_vote_ignores_unparseable_and_reports_ties():
    assert majority([THINK, THINK, NO_THINK]) == THINK
    assert majority([THINK, None, None]) == THINK
    assert majority([THINK, NO_THINK]) is None
    assert majority([None, None]) is None


def _record(case, predicted, *, attempt=0, error=None, wall_ms=100.0):
    return {
        "model": "m",
        "case": case,
        "attempt": attempt,
        "raw": predicted or "",
        "predicted": predicted,
        "wall_ms": wall_ms,
        "prompt_eval_ms": 50.0,
        "eval_ms": 20.0,
        **({"error": error} if error else {}),
    }


TINY_CASES = [
    {"text": "hola", "label": NO_THINK, "lang": "es", "category": "chit-chat"},
    {"text": "riddle", "label": THINK, "lang": "en", "category": "logic"},
    {"text": "bonjour", "label": NO_THINK, "lang": "fr", "category": "chit-chat"},
]


def test_summarize_computes_accuracy_recalls_and_consistency():
    records = [
        # case 0 (NO_THINK): 2 of 3 right -> majority right, inconsistent
        _record(0, NO_THINK, attempt=0),
        _record(0, NO_THINK, attempt=1),
        _record(0, THINK, attempt=2),
        # case 1 (THINK): all wrong -> missed THINK
        _record(1, NO_THINK, attempt=0),
        _record(1, NO_THINK, attempt=1),
        _record(1, NO_THINK, attempt=2),
        # case 2 (NO_THINK): all right
        _record(2, NO_THINK, attempt=0),
        _record(2, NO_THINK, attempt=1),
        _record(2, NO_THINK, attempt=2),
    ]

    s = summarize(records, TINY_CASES)

    assert s["cases"] == 3 and s["calls"] == 9 and s["errors"] == 0
    assert s["per_call_accuracy"] == pytest.approx(5 / 9)
    assert s["majority_accuracy"] == pytest.approx(2 / 3)
    assert s["consistency"] == pytest.approx(2 / 3)
    assert s["confusion"] == {"tp": 0, "fn": 1, "fp": 0, "tn": 2}
    assert s["think_recall"] == 0.0
    assert s["no_think_recall"] == 1.0
    assert s["think_precision"] is None  # never predicted THINK by majority
    assert s["per_lang_accuracy"] == {"en": 0.0, "es": 1.0, "fr": 1.0}
    assert s["per_category_accuracy"] == {"chit-chat": 1.0, "logic": 0.0}
    assert [m["text"] for m in s["misclassified"]] == ["riddle"]
    assert s["latency_ms"]["median"] == 100.0


def test_summarize_separates_errors_unparseable_and_ties():
    records = [
        _record(0, None, attempt=0, error="boom"),  # transport error, not scored
        _record(0, None, attempt=1),  # model said something else
        _record(1, THINK, attempt=0),
        _record(1, NO_THINK, attempt=1),  # genuine tie
        _record(2, NO_THINK, attempt=0),
    ]

    s = summarize(records, TINY_CASES)

    assert s["errors"] == 1
    assert s["unparseable_calls"] == 1
    assert s["ties"] == 1
    assert s["majority_accuracy"] == pytest.approx(1 / 3)


def test_baseline_accuracy_is_majority_class_share():
    assert baseline_accuracy(TINY_CASES) == pytest.approx(2 / 3)


# --- dataset sanity: a wrong label here silently skews every benchmark run ---


def test_dataset_cases_are_well_formed():
    for case in CASES:
        assert set(case) == {"text", "label", "lang", "category"}
        assert case["label"] in (THINK, NO_THINK)
        assert case["text"].strip() == case["text"] and case["text"]
        assert case["lang"] in {"es", "en", "fr", "pt", "it", "de"}


def test_dataset_has_no_duplicate_texts():
    texts = [case["text"] for case in CASES]
    assert len(texts) == len(set(texts))


def test_dataset_is_reasonably_balanced_and_multilingual():
    labels = Counter(case["label"] for case in CASES)
    assert min(labels.values()) / len(CASES) >= 0.35, labels
    langs = Counter(case["lang"] for case in CASES)
    assert {"es", "en", "fr"} <= set(langs)
    # both classes represented in each of the three main languages
    for lang in ("es", "en", "fr"):
        assert {c["label"] for c in CASES if c["lang"] == lang} == {THINK, NO_THINK}


def test_dataset_covers_adversarial_cases_in_both_directions():
    categories = {case["category"] for case in CASES}
    assert "adversarial-trivial" in categories  # says "think carefully", needs no thinking
    assert "word-problem-trap" in categories  # looks trivial, needs thinking


def test_few_shot_examples_do_not_leak_into_the_dataset():
    prompt = ROUTER_SYSTEM_PROMPT.lower()
    for case in CASES:
        assert case["text"].lower() not in prompt
