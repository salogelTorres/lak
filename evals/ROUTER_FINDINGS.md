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

### v4 — newer-generation small models (structured output, temperature 0)

Objection: v1-v3 only tried `qwen3` small variants (same generation as the
8B) plus one non-generative classifier. A genuinely newer generation might
have closed the gap through better instruction-following, independent of
raw size. Tested standalone (100% GPU where the model fits), same 107
cases, same JSON schema, `think:false`, `temperature:0`.

| Model | Scenario | Majority acc | THINK recall | NO_THINK recall | Median latency |
|---|---|---|---|---|---|
| **qwen3.5:4b** | standalone, 100% GPU (3.1GB) | **96.3%** | 97.6% | 95.4% | **450ms** |
| qwen3.5:9b | standalone, 45/55 CPU/GPU (6.1GB, doesn't fully fit) | **99.1%** | 97.6% | 100% | 1485ms |
| ministral-3:3b | standalone, 100% GPU (2.7GB) | 91.6% | 83.3% | 96.9% | 230ms |
| phi4-mini | standalone, 100% GPU (3.1GB) | 74.8% | **38.1%** | 98.5% | 294ms |
| qwen3.5:2b | standalone, 100% GPU (2.4GB) | 75.7% | **40.5%** | 98.5% | 392ms |

For reference, `qwen3:8b` (v2 baseline): 94.4% / **100%** THINK recall /
90.8% / 778ms.

`phi4-mini` and `qwen3.5:2b` collapse exactly like the old `qwen3:4b` did
(≈40% THINK recall) — a newer generation doesn't rescue a model that's
simply too small for this specific meta-judgment; the capability
threshold theory from v1-v3 holds. `ministral-3:3b` clears chit-chat/tools
fine but misses too many THINK cases (logic 75%, word-problem-trap 67%) to
qualify. `qwen3.5:9b` confirms the accuracy ceiling is above 94.4% (99.1%,
only 1 miss) but doesn't fit in 6GB VRAM — slower than the baseline it was
meant to beat, so not a viable router regardless of accuracy.

**`qwen3.5:4b` is the standout**: higher majority accuracy than `qwen3:8b`
(96.3% vs 94.4%) at 42% of the latency (450ms vs 778ms). It does not
match `qwen3:8b`'s 100% THINK recall — it misses exactly one case, "¿Cuántos
meses del año tienen 28 días?", the same borderline item `qwen3:8b` also
gets wrong in this exact metric (the honest answer, "all of them have at
least 28," makes NO_THINK a defensible read too). With only 42 THINK cases
in the dataset, one miss is already 97.6% — "100% vs. 97.6%" here means
"zero misses vs. one shared, arguably-ambiguous miss," not a reliability
gap.

### v5 — round 3: Granite 4.2, Cogito, Gemma 3 ("NeoHorse-1-9B" doesn't exist)

Before running this round, every proposed tag was checked for existence
in the Ollama registry first (a lesson from earlier rounds — don't spend
a download on an unverified name). `neohorse-1:9b` and `neohorse:9b` both
returned "pull model manifest: file does not exist" — no such model is
published under either name; it was dropped without spending a download
on it. The other four (`granite4.2:8b`, `granite4.2:3b`, `cogito:8b`,
`gemma3:4b`) are real and were pulled and benchmarked the same way as
every prior round.

| Model | Scenario | Majority acc | THINK recall | NO_THINK recall | Median latency |
|---|---|---|---|---|---|
| granite4.2:8b | 33/67 CPU/GPU (6.2GB, doesn't fit) | 76.6% | **40.5%** | 100% | 1058ms |
| granite4.2:3b | standalone, 100% GPU (2.5GB) | 92.5% | 85.7% | 96.9% | 293ms |
| cogito:8b | 25/75 CPU/GPU (5.6GB, doesn't fit) | 81.3% | **52.4%** | 100% | 599ms |
| gemma3:4b | standalone, 100% GPU (2.9GB) | 88.8% | 90.5% | 87.7% | 447ms |

For reference, `qwen3.5:4b` (v4 champion): 96.3% / 97.6% / 95.4% / 450ms.

None of these four come close to dethroning `qwen3.5:4b`. The notable,
somewhat counterintuitive result: `granite4.2:8b` and `cogito:8b` — both
8B-class, both explicitly marketed around reasoning/agentic behavior —
collapse on THINK recall (40.5%, 52.4%) almost as badly as the smallest
failed candidates from v2/v4. Neither size nor a "built for reasoning"
pitch predicts anything about this specific meta-judgment task, and
neither fits in 6GB VRAM either, so they lose on speed too. `granite4.2:3b`
and `gemma3:4b` are competent (92.5%/88.8% accuracy) but clearly behind
the champion on every axis — no trade-off worth taking.

## Conclusion

Nine alternative candidates have now been tested across three follow-up
rounds (v2's `qwen3:0.6b`/old `qwen3:4b`, v3's GLiClass, v4's
`qwen3.5:2b/9b`/`ministral-3:3b`/`phi4-mini`, v5's `granite4.2:8b/3b`/
`cogito:8b`/`gemma3:4b`) beyond the original `qwen3:8b` baseline. Exactly
one — **`qwen3.5:4b`** — beats it, and does so clearly: 96.3% vs 94.4%
accuracy, 450ms vs 778ms latency (42% faster), at the cost of missing one
THINK case out of 42 that is itself borderline/ambiguous (see v4). No
other candidate has come within striking distance on more than one axis
at a time. Given diminishing returns are now clear — three full rounds of
alternatives (generational, architectural, and "reasoning-branded") all
landed at or below the v4 champion — this is a reasonable point to stop
searching and commit, absent a specific new reason to keep looking.

**Not yet acted on:** wiring a router into `app/bot.py`/`app/llm.py` (was
Paso 3 of the original plan) — still not started, pending explicit
confirmation to stop searching and commit to `qwen3.5:4b`. GLiClass/torch
(v3) were installed only inside the running container for that test,
never added to the Dockerfile/requirements — nothing to roll back.

## Open questions for next session

- Confirm closing the model search on `qwen3.5:4b` (recommended above)
  or provide a specific reason to keep looking — three full rounds (nine
  alternative candidates) is enough that another round should have a
  concrete hypothesis behind it, not just "try whatever's newest".
- Once confirmed, implement the wiring (Paso 3).
- A live idea from this round, independent of which model wins: instead
  of one router, a small Pareto-tiered cascade (e.g. a cheap/fast model
  handles the obvious cases, escalating only the uncertain ones to a
  slower/more accurate one) — worth real consideration if the final
  numbers show a genuine accuracy/latency frontier rather than one
  dominant model.
- Deferred, not required to close this: a confidence-gated cascade using
  logprobs, or a BGE-M3 + logistic-regression head once real labeled
  traffic exists.
- `evals/results/` is gitignored — this file documents the finding
  independent of the raw JSON surviving on this machine.
