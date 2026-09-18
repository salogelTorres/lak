# THINK/NO_THINK router: model comparison findings

**Date:** 2026-09-18
**Motivation:** `think_harder` (a tool the model self-invokes to get extended
reasoning) never fired on real Telegram messages — 0/5 attempts, including
ones explicitly saying "piénsalo bien". A pre-classification step (decide
THINK/NO_THINK *before* the main reply) was proposed instead. This
benchmarks which model can do that classification reliably and fast.

**Method:** `evals/router_bench.py` + `evals/router_dataset.py` (107
labeled cases, multilingual es/en/fr/pt/it/de, adversarial in both
directions — trivial questions dressed up as "think carefully", and
lexically trivial riddles that hide a trap). Run via `bench.py` against
Billy's Ollama (RTX 4050, 6GB VRAM / 5GB usable). 3 attempts per case.

Two prompting techniques were tested:
1. **Free text**, "reply with one word" instruction, `num_predict: 5`.
2. **Structured output**: Ollama `format` JSON schema (`{"label":
   "THINK"|"NO_THINK"}`), `num_predict: 20`, `temperature: 0`.

## Results

### v1 — free text, default temperature

| Model | Scenario | Majority acc | THINK recall | NO_THINK recall | Median latency |
|---|---|---|---|---|---|
| qwen3:8b | colocated w/ itself | 98.1% | 97.6% | 98.5% | 5010ms |
| qwen3:0.6b | colocated w/ 8b | 60.7% | **0.0%** | 100% | 28ms |
| qwen3:4b | standalone, 100% GPU | — | — | — | **100% unparseable** — model ignores the "one word" instruction, rambles ("Okay, let's see...") regardless of `num_predict` budget (tested up to 60 tokens, never reaches an answer) |

### v2 — structured output (JSON schema), temperature 0

| Model | Scenario | Majority acc | THINK recall | NO_THINK recall | Median latency |
|---|---|---|---|---|---|
| **qwen3:8b** | colocated w/ itself | **94.4%** | **100%** | 90.8% | **778ms** |
| qwen3:0.6b | colocated w/ 8b | 68.2% | 73.8% | 64.6% | 202ms |
| qwen3:4b | standalone, 100% GPU | 43.9% (worse than the 60.7% always-NO_THINK baseline) | 100% | **7.7%** | 369ms |

Raw per-call JSON for every run lives in `evals/results/`
(`router_bench_qwen3-*.json` / `*_v2.json`) — gitignored, host-local only.

### v3 — GLiClass multilang-mini (encoder classifier, not generative)

A fair objection to "small models don't classify well" was raised: `qwen3
0.6b/4b` are generative LMs pressed into classifying, not a purpose-built
classifier. [GLiClass](https://github.com/knowledgator/gliclass)
(`knowledgator/gliclass-multilang-mini`, ~284M, multilingual zero-shot
single/multi-label classification) is architecturally the right kind of
tool for this, so it deserved its own test before ruling out "any small
model" — installed temporarily (`pip install torch --index-url
https://download.pytorch.org/whl/cpu gliclass`) inside the running bot
container, no lasting changes, run against the exact same 107 cases via
`evals.router_bench.summarize`/`baseline_accuracy` for directly
comparable numbers.

| Model | Majority acc | THINK recall | NO_THINK recall | Median latency |
|---|---|---|---|---|
| gliclass-multilang-mini | **39.3%** (worse than the 60.7% baseline) | 100% | **0.0%** | 321ms |

It labels **every single case** "needs careful step-by-step reasoning"
(~99% confidence each time), regardless of prompt, few-shot examples, or
label wording tried. A sanity check confirms this isn't a misuse bug: the
same pipeline nails a plain sentiment task (`positive`/`negative`, 100%
confidence, both directions correct) instantly. The model works — it just
hasn't learned "does this need reasoning" as a property; unlike
sentiment/topic, that isn't lexically or topically groundable, and
GLiClass's training data (commonsense_qa + logic datasets, per its model
card) apparently didn't teach it either. Per the pre-agreed bar ("85-90%
→ the discussion is over"), this ends it decisively — no closer to a
verdict than "worse than guessing."

## Conclusion

**No small or purpose-built classifier beats `qwen3:8b` on this task —
not `qwen3:0.6b`/`4b` (a prompting/format problem, partially fixable),
and not GLiClass (a genuine capability gap, not fixable by prompting).**
`qwen3:8b` itself is the router: structured output + temperature 0 cut
its latency from 5.0s to 0.78s (6.4x) while keeping THINK recall at 100%
(never misses a case that genuinely needs reasoning — the expensive kind
of error). The 9.2% false-positive rate on NO_THINK cases (over-triggering
on a few easy ones) only costs latency, not quality.

**Decision: wire `qwen3:8b` as its own router** (structured output,
`think:false`, `temperature:0`) into `app/bot.py`/`app/llm.py` before the
main reply, gating the real `think:true` call on its decision. Cost:
~0.8s added per message to unlock extended reasoning (currently
5-10+ min unconditionally) only when actually warranted. GLiClass/torch
were installed only inside the running container for this test, never
added to the Dockerfile/requirements — nothing to roll back.

## Open questions for next session

- Implement the wiring above (was Paso 3 of the original plan).
- Optional, not required to close this: a confidence-gated cascade
  (skip the router call outright on lexically obvious cases) or the
  BGE-M3 + logistic-regression head once real labeled traffic exists —
  both deferred, no model available today makes them necessary.
- `evals/results/` is gitignored — this file documents the finding
  independent of the raw JSON surviving on this machine.
