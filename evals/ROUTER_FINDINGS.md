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

## Conclusion

**Neither small model works, and it isn't a prompting problem.** With the
format fixed, `qwen3:0.6b` is still mediocre and inconsistent across
categories. `qwen3:4b` is *worse than guessing*: it says THINK for almost
everything (7.7% NO_THINK recall — e.g. misclassifies "hola" and "15+27").
This looks like a genuine judgment-capacity gap in smaller Qwen models for
this specific semantic task ("does this need reasoning"), not something a
better prompt or output format fixes.

**`qwen3:8b` itself is the only viable router**, and structured output +
temperature 0 cut its latency from 5.0s to 0.78s (6.4x) while keeping
THINK recall at 100% (never misses a case that genuinely needs reasoning —
the expensive kind of error). The 9.2% false-positive rate on NO_THINK
cases (over-triggering on a few easy ones) only costs latency, not quality.

**Revised plan (pending confirmation, not yet implemented):** no separate
router model, no GLiClass. Wire `qwen3:8b` as its own router (structured
output, `think:false`, `temperature:0`) into `app/bot.py`/`app/llm.py`
before the main reply, gating the real `think:true` call on its decision.
Cost: ~0.8s added per message to unlock extended reasoning (currently
5-10+ min unconditionally) only when actually warranted.

## Open questions for next session

- Confirm and implement the wiring above (was Paso 3 of the original
  plan, now simplified — no model switch needed).
- Worth trying: lowering the decision threshold, or a quick check with
  `qwen3:1.7b` (untested; likely to share the small-model judgment gap).
- `evals/results/` is gitignored — this file documents the finding
  independent of the raw JSON surviving on this machine.
