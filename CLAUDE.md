# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **template** for a Telegram bot backed by an LLM (local via a containerized
Ollama, or remote via any OpenAI-compatible API), fully dockerized. It is not
meant to be developed in place and deployed once — it's cloned per agent
instance (one clone = one bot = one Telegram token), configured via
`setup.py`, and run with `docker compose up`. Read `README.md` first; it's
the source of truth for user-facing setup/usage instructions and is kept in
sync with the code — update it alongside any behavioral change here.

## Commands

```bash
# Dev environment (only needed to run the test suite; setup.py itself has no deps)
python -m venv .venv
.venv/Scripts/activate          # Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt

pytest                                          # full suite, coverage enforced
pytest tests/test_bot.py                        # one file
pytest tests/test_bot.py::test_start_replies_with_greeting   # one test
pytest -k "llm_backend"                         # by keyword

python setup.py                 # interactive wizard: writes .env, system_prompt.txt,
                                 # docker-compose.override.yml, then docker compose up
python update.py                # existing agent: fetch+merge template/main, fill in
                                 # any new .env keys, then docker compose up -d --build
docker compose up -d --build    # run without the wizard (needs .env already present)
docker compose logs -f          # follow bot + ollama logs
docker compose exec ollama ollama pull <model>   # pull/switch a local model
docker compose exec bot python -m evals.run      # manual tool-use evals against a real LLM
```

Coverage is enforced at 99% (line+branch) via `--cov-fail-under=99` in
`pyproject.toml`; `pytest` fails outright if a change drops it below that.
The whole suite mocks all I/O (`httpx`, `input()`, `subprocess`) — no Docker,
network, or real Telegram/LLM credentials are needed to run it.

## Architecture

**`setup.py`** (repo root, stdlib-only, not part of the `app` package) is the
onboarding wizard. It intentionally asks only for values that make sense to
customize per agent (`BASE_KEYS` + backend-specific `BACKEND_KEYS`) and
leaves everything else — including `SYSTEM_PROMPT_FILE` and the `*_BASE_URL`
keys — at its `.env.example` default. This split exists because of a real
failure mode: earlier versions asked for every `.env.example` key verbatim,
and a user ended up typing free-text personality instructions into the
`SYSTEM_PROMPT_FILE` path variable, and a raw `LLM_BACKEND` value that wasn't
validated, crash-looping the container. `ask_llm_backend` now validates in a
loop and accepts natural aliases (`local`→`ollama`, `cloud`/`api`/`remote`);
personality text goes through the separate `apply_personality()` step that
appends to `system_prompt.txt`, never into `.env`. Keep this separation when
touching the wizard — don't add new keys to the interactive prompts unless a
user genuinely needs to set them per agent.

`setup.py` also auto-detects an NVIDIA GPU (`shutil.which("nvidia-smi")`) and
writes `docker-compose.override.yml` from `docker-compose.override.yml.example`
so Compose picks up GPU acceleration for the `ollama` service with no extra
flags. CPU-only inference is slow enough (20-30+s/reply for an 8B model) to
look indistinguishable from the bot being broken, so this isn't optional
polish — it's load-bearing for the bot being usable.

**Gitignored, per-instance/per-host files** — `.env`, `app/prompts/system_prompt.txt`,
`docker-compose.override.yml` — are the whole reason multiple agents can
share this template safely. Each has a tracked `.example` counterpart, and
`setup.py` populates the real file only if it doesn't already exist ("never
clobber personalization/host config" is a hard invariant — see
`ensure_system_prompt()` / `ensure_gpu_override()`). This is what lets an
already-configured agent run **`update.py`** (repo root, imports `setup` and
reuses its `ROOT`/`ENV_FILE`/`parse_env_example`/`ensure_*` functions rather
than duplicating them) to fetch+merge `template/main` and rebuild without
losing its token, personality, or GPU config. `update.py` also back-fills
any `.env.example` key a merge introduces that isn't in the agent's `.env`
yet (`fill_in_new_env_keys()`) — this is why any new per-agent setting must
follow the same pattern as existing ones: default committed as
`<name>.example`, real file/key gitignored-or-backfilled, never silently
required.

**Runtime code** (`app/`), wired together in `app/main.py`:
- `config.py` — `Config.load()` reads env vars (via `python-dotenv`, though
  in the container Compose already injects them) into a single dataclass,
  validates `LLM_BACKEND` is `ollama`/`cloud`, and resolves the
  `{{AGENT_NAME}}` placeholder in the system prompt at load time.
  `router_model` (`ROUTER_MODEL` env var, empty by default) is read
  unconditionally regardless of backend — it's `app/main.py`, not this
  file, that decides whether it actually gets used (see `router.py` below).
- `llm.py` — `LLMClient` Protocol with `OllamaClient` and `CloudClient`
  (any OpenAI-compatible `/chat/completions` endpoint); `build_llm_client()`
  picks one from `Config.llm_backend`. Both are thin `httpx` wrappers (via
  the shared `_post_json()` helper) with no retry/streaming logic. Each
  implements `chat()` as a thin per-backend `complete()` closure (shapes its
  own request payload/endpoint) handed to the shared `_run_with_tools()`
  loop, which is what actually knows how to run tool calls — up to
  `MAX_TOOL_ROUNDS` rounds, forcing a final tools-withheld round so a model
  that won't stop requesting tools can't loop forever. Ollama's `/api/chat`
  and OpenAI-compatible `/chat/completions` both speak the same
  `tool_calls`/`role: "tool"` shape, which is what makes one shared loop
  possible instead of duplicating it per backend. Tool execution itself
  (`_call_tool()`) runs the matched `Tool.execute` via `asyncio.to_thread`
  (tools are sync, may block on network I/O) and never lets a tool's
  exception escape to the model — it becomes a `"...tool failed to run"`
  message instead, same philosophy as the rest of the bot: a broken
  side-capability shouldn't break the conversation. `chat()` also takes a
  `think: bool = False` kwarg, threaded through `_run_with_tools()` into
  every `complete()` call for that reply (both the no-tools branch and each
  round of the tool-calling loop) — this is what `router.py` below flips on
  per-message. `CloudClient`'s `complete()` closure ignores it; there's no
  OpenAI-compatible equivalent. This is separate from `_with_think_harder()`,
  which still always forces `think=True` for the self-invoked
  `think_harder` tool's own re-ask, independent of the router.
- `router.py` — `OllamaRouter.classify(text) -> bool` is a small, separate
  classification call, made before every reply on the `ollama` backend when
  `Config.router_model` is set, that decides THINK/NO_THINK directly and
  feeds the result into `chat(..., think=...)` above. This exists because
  `think_harder` (the self-invoked tool, below) turned out to be an
  unreliable mechanism in practice — it stayed silent even on messages
  explicitly asking to "think carefully" — while asking a model to classify
  the message directly is a much stronger signal. `evals/router_bench.py` +
  `evals/router_dataset.py` (a labeled, multilingual,
  adversarial-in-both-directions dataset) benchmarked nine Ollama models
  against this exact question before `evals/ROUTER_FINDINGS.md` settled on
  a prompt/schema; `router_bench.py` imports `ROUTER_SYSTEM_PROMPT` and
  `parse_label` from this module rather than duplicating them, so that
  benchmark measures exactly what production runs, not a copy that could
  drift from it. `classify()` uses Ollama's structured-output `format`
  (a JSON schema constraining the next token to the enum, not a free-text
  "reply with one word" instruction some models otherwise ramble past
  indefinitely) and fails open — any network error, non-2xx response, or
  unparseable label logs a warning and returns `False` — since a broken
  router must never block a reply, only skip the speed-up it would have
  bought. It classifies only the latest user message directly via its own
  `httpx.AsyncClient`, independent of `_post_json()`. Router and principal
  model share the same Ollama instance's VRAM, so picking a router model is
  a hardware-fit question as much as an accuracy one — see
  `evals/ROUTER_FINDINGS.md` for why the template's own reference
  deployment ended up using the same model for both.
- `tools/` — the catalog of capabilities an agent *can* use, entirely
  separate from which ones it *does*: nothing here is wired into an agent by
  default. `tools/base.py` defines `Tool` (name, description, JSON-schema
  `parameters`, sync `execute`); each tool is its own module (e.g.
  `tools/web_search.py`) exporting a `TOOL` instance, registered in
  `tools/__init__.py`'s `AVAILABLE_TOOLS`. An agent opts in per tool via
  `Config.enabled_tools` (the `ENABLED_TOOLS` env var), resolved against the
  catalog by `resolve_tools()` — unknown names are silently ignored rather
  than erroring, so removing a tool from the template doesn't break an
  agent that still lists it. `bot.py`'s `_reply_to()` is the only caller:
  it resolves tools once per message and only passes a `tools=` kwarg to
  `llm_client.chat()` when the list is non-empty, so an agent with no tools
  enabled exercises the exact same code path as before tools existed.
  `web_search.py` hits DuckDuckGo's HTML endpoint directly (no API key, no
  extra dependency) and redacts anything in a result that looks like a
  prompt-injection attempt before it ever reaches the model — a search
  result is untrusted content. `fetch_page.py` complements it for deeper
  research: the model can fetch a specific URL (typically one `search_web`
  just returned) and read its full text instead of a snippet, truncated to
  `MAX_CHARS` so one page can't dominate the context budget. Both tools
  share the same markup-stripping/URL-normalizing/injection-detection logic
  via `tools/_html.py` rather than duplicating it — keep any new
  HTML-scraping tool on that shared module too, since letting the
  injection-redaction rules drift apart per tool is exactly the kind of
  thing that's easy to miss. `get_weather` (`weather.py`) is a stateless
  two-request lookup against Open-Meteo (geocode a place name, then fetch
  its forecast), no API key needed, same never-raise-on-failure philosophy
  as the other two.

  `memory.py` (`remember`/`recall`) and `reminders.py` (`remind_me`) are
  different: they need to know *which chat* they're running in, which the
  model must never supply itself (it could get it wrong, or a user could
  try to make it target another chat). `tools/base.py`'s `ToolContext`
  (`chat_id`, a `schedule_reminder` callback, and a `think_harder` callback
  — see below) is injected by `app.llm._call_tool()` for any `Tool` with
  `needs_context=True`, threaded in from `bot.py`'s `_make_tool_context()`
  — never sourced from the model's own arguments. `remember`/`recall`
  persist to a single JSON file
  (`MEMORY_FILE`, default `/data/memory/memory.json`, keyed by `chat_id`,
  guarded by a `threading.Lock` since tool execution runs in a thread pool)
  backed by the `memory_data` volume in `docker-compose.yml`, so notes
  survive restarts unlike the in-memory conversation history. `remind_me`
  doesn't deliver anything itself — it validates the request and hands off
  to `context.schedule_reminder`, which `bot.py` implements with
  `asyncio.sleep` inside a coroutine scheduled via
  `asyncio.run_coroutine_threadsafe()` onto the main loop captured (via
  `asyncio.get_running_loop()`) when `_make_tool_context()` builds the
  context — **not** a bare `asyncio.create_task()`: every tool, regardless
  of `needs_context`, runs through `asyncio.to_thread()` (see
  `app.llm._call_tool`), so `schedule_reminder()` always executes on a
  worker thread with no event loop of its own, where `create_task()` raises
  `RuntimeError: no running event loop` (this shipped broken — it only
  surfaced against a real Telegram conversation, since tests exercised
  `schedule_reminder()` from the main thread directly). The returned
  `Future` gets the same GC-safety treatment as the warm-up task below
  (held in `application.bot_data` until an `add_done_callback()` — not
  code inside the coroutine closing over the `Future` variable, which
  would race the cross-thread scheduling — removes it once done). No real
  job queue here either way: like conversation history, a pending reminder
  is lost if the bot restarts before it fires — acceptable for this
  template, but worth knowing.

  `think_harder.py` is a different kind of context-dependent tool: instead
  of `chat_id`, it needs `context.think_harder` — a callback owned by
  `app.llm._with_think_harder()`, rebuilt every round of the tool-calling
  loop in `_run_with_tools()` from a *snapshot of that round's conversation*
  taken before the tool-call turn is appended, plus the backend's own
  `complete()` closure. Calling it re-sends that exact conversation with
  `think=True` (Ollama's extended-reasoning flag; ignored by `CloudClient`,
  where it degrades to a plain re-ask) and returns just the final
  `content`, discarding the reasoning trace — bot.py never sees or relays
  it. The tool wraps that answer with an instruction telling the outer,
  non-thinking model to relay it verbatim rather than rephrase it, same
  trust model already at play for every other tool's results. Because
  `Tool.execute` is sync but `complete()` is async, the callback bridges
  with a fresh `asyncio.run()` inside the worker thread `_call_tool()`
  already runs tools in via `asyncio.to_thread` — safe since that thread
  has no event loop of its own to conflict with. This self-invoked path is
  what `router.py`'s `OllamaRouter` above exists to route around — an agent
  with `ROUTER_MODEL` set doesn't need the model to reach for this tool at
  all, since `bot.py` decides `think` up front instead. Letting the model
  self-invoke it *on top of* that turned out not to be harmless: it stacks
  a second full reasoning round onto a reply that's already thinking, and
  since the tool-call announcement reuses the exact same "🤔 Thinking it
  through..." text as the router's own notice, the user just sees a
  duplicate message with no clue an extra, redundant LLM call is what
  actually happened in between — this shipped and was caught live against
  Billy. `bot.py`'s `_reply_to()` fixes this by excluding `think_harder`
  from the tools offered to the model whenever `think` is already `True`
  for that turn; a router-less agent (or one where the router said
  `NO_THINK`) still gets it offered normally.

  Every tool call is also announced to the chat right before it runs
  (`bot.py`'s `_make_on_tool_call()`, threaded into `_run_with_tools()` as
  `on_tool_call`) via `TOOL_CALL_LABELS`, so a call that takes a few seconds
  doesn't look like the bot has stalled. `_run_with_tools()` parses each
  call's arguments once (`_parse_arguments()`, shared with `_call_tool()`
  so the Ollama-dict-vs-OpenAI-string handling doesn't drift between the
  two) and hands them to `on_tool_call`, so `TOOL_CALL_LABELS`' formatters
  can say *what* it's doing — the query, the URL, the note — not just that
  it's doing something. Each formatter falls back to a plain label if its
  argument is missing, and `_make_on_tool_call()` catches any exception a
  formatter raises (a model sending an odd argument type must not take the
  whole reply down with it); a tool with no entry there still gets a
  generic `"🔧 Using {name}..."` message rather than silence.
- `bot.py` — `build_application(config, llm_client, router=None)` wires
  `python-telegram-bot` handlers; `router` is an optional `OllamaRouter`
  (see `router.py` above), constructed once in `app/main.py` and threaded
  through, not built per-message. Inside `_reply_to()`, right after history
  is trimmed and before tools are resolved, `think = await
  router.classify(text) if router else False` — a router-less agent (the
  default) always passes `think=False`, the same as before the router
  existed. When it comes back `True`, the chat gets a
  `TOOL_CALL_LABELS["think_harder"]` notice (reused rather than a
  duplicate string) before the LLM call, and `think=think` is passed to
  `llm_client.chat()` in both the tools and no-tools branches.
  Conversation history is an in-memory `dict[chat_id, list[message]]` closed
  over inside `build_application` (lost on restart), not a module-level or
  persisted store — alongside a second `dict[chat_id, str]` holding each
  chat's running summary. It's capped by `_trim_to_token_budget()` against
  `Config.max_history_tokens` (a rough ~4-chars/token estimate, not a real
  tokenizer — see `_estimate_tokens`) as a last-resort safety net, dropping
  the *oldest* messages first regardless of how many that is; the system
  message and the newest message are always kept even if the newest alone
  exceeds budget. This replaced an earlier fixed 20-message cap — don't
  reintroduce a message-count limit; a handful of long messages can blow a
  context window just as easily as many short ones. Before that safety net
  kicks in, `_reply_to()` prefers **compaction** over dropping: once total
  history exceeds `max_history_tokens`, `_split_recent()` peels off
  everything older than the trailing `Config.recent_history_tokens`, and
  `_compact_history()` asks the LLM to fold those older messages (plus any
  existing summary) into an updated short summary, which
  `_build_system_message()` then appends to the system prompt instead of the
  raw messages. This is a batch operation — it only fires once the "older"
  bucket is non-empty, not on every message near the threshold — and a
  Telegram notice (`COMPACTING_NOTICE`) goes out first since it's an extra
  LLM call. If that call fails, the exception is swallowed (logged) and
  `_trim_to_token_budget()` falls back to plain dropping for that turn, so a
  broken compaction never breaks the actual reply. Trimming happens *before*
  the LLM call in `_reply_to()`, so it bounds what's actually sent, not just
  what's stored. `handle_message`
  (text) and `handle_voice` (voice notes/audio files) both funnel through the
  shared `_reply_to()` closure (access control, history, typing indicator,
  LLM call, error handling, trimming) — add new input types the same way
  rather than duplicating that logic. `post_init` fires `_warm_up_ollama` via
  `asyncio.create_task` and stores the task on `application.bot_data`, not
  just as a local variable — asyncio only holds a *weak* reference to a
  task otherwise, so an unstored fire-and-forget task can be
  garbage-collected mid-run; keep this pattern for any future background
  task started the same way. Voice notes are transcribed with
  `faster-whisper` (`_transcribe_sync`, run off the event loop via
  `asyncio.to_thread` since it's a blocking CPU call) and always prefixed
  with `VOICE_TRANSCRIPTION_PREFIX` before being added to history, so the
  model can tell a message was spoken vs. typed — the system prompt template
  explains the convention. The `WhisperModel` instance is cached per model
  name in the module-level `_whisper_models` dict (loading one is slow), not
  reloaded per message. The final reply goes out through
  `_send_formatted_reply()` with `parse_mode=ParseMode.MARKDOWN` — models
  naturally write Markdown (`**bold**`, `[text](url)`, ...) and Telegram
  shows that as literal unrendered symbols without a parse mode set. Legacy
  Markdown, not `MarkdownV2`: it doesn't demand escaping every stray
  `.`/`-`/`!` outside markdown constructs the way `MarkdownV2` does, which
  model output never does either. If the reply isn't valid even under that
  laxer parser (an unbalanced `*`/`_`/`` ` ``), Telegram raises
  `BadRequest` and `_send_formatted_reply()` retries once with no parse
  mode at all — a formatting quirk must never eat the reply outright.

**`evals/`** (repo root, outside the `app` package) is a manual eval suite,
separate from `tests/`: it calls the real configured backend and judges the
model's own tool-use choices — does it call `search_web` for a
current-events question, reach for `fetch_page` when a snippet isn't
enough, call `get_weather` *and* actually report a temperature from it,
schedule a sane (positive-delay, non-empty-message) reminder via
`remind_me`, actually get a real answer back from `think_harder` (not one
of its fallback strings) on a tricky reasoning question, stay quiet on
tools for chit-chat. It's slow and not fully
deterministic, so it never runs as part of `pytest` and isn't subject to
the coverage gate — run it by hand with `python -m evals.run` (usually via
`docker compose exec bot`, so `OLLAMA_BASE_URL`'s default resolves over the
Compose network). It spies on `app.llm._call_tool` by monkeypatching the
module attribute for the duration of each case rather than instrumenting
the real code path, so production behavior is untouched by the eval
harness existing. The `remember`/`recall` case is the strongest one: rather
than checking a tool got called, it points `memory.MEMORY_FILE` at a throwaway
temp file and verifies a fact saved in one exchange is correctly surfaced
back in a *separate* one — real persistence, not just tool selection.

**`bench.py` + `evals/router_bench.py`/`router_dataset.py`** answer a
narrower, prior question for the `ollama` backend: *which small model can
reliably decide THINK vs. NO_THINK before the real reply*, since that
routing call has to be cheap and fast, unlike the reasoning it gates. This
came out of watching `qwen3:8b` never call `think_harder` on real
Telegram messages, including ones explicitly asking it to "think
carefully" — self-directed tool-calling for reasoning turned out to be a
much weaker signal than the model just being asked to classify. The
dataset is deliberately multilingual (the router must not key on the
user's language) and adversarial in both directions: lexically trivial
wording that hides a trap (`word-problem-trap`), and trivial questions
dressed up with "think carefully" (`adversarial-trivial`). `bench.py`
(repo root, reuses `setup.ensure_docker_running`/`pull_ollama_model` same
as `update.py` reuses `setup`'s other pieces) pulls whatever models are
missing, then runs `evals/router_bench.py` inside the `bot` container via
`docker compose exec` — `router_bench.py` itself only needs `httpx` and a
reachable Ollama, so it also runs standalone with `--base-url` pointed
elsewhere. It measures THINK-recall and NO_THINK-recall separately
(missing a real THINK case costs quality; false-triggering on an easy one
costs latency — they're not symmetric) plus per-language and
per-category accuracy and consistency across repeated attempts, and
writes every raw call to `evals/results/*.json` (gitignored; bind-mounted
in `docker-compose.yml` so a run inside the container is visible on the
host). Same rule as the other two eval tools: never runs under `pytest`.
`tests/test_router_bench.py` covers only the pure parts (label parsing,
majority voting, metric computation, dataset shape) that would silently
skew every benchmark run if wrong — the actual benchmarking is Ollama
calls, so it can't be unit-tested.

**Docker**: `docker-compose.yml` defines `bot` and `ollama` as separate
services on the Compose network; the bot always reaches Ollama at
`http://ollama:11434` regardless of backend choice (the `ollama` service
just sits idle if `LLM_BACKEND=cloud`). `app/prompts/` is bind-mounted into
the container read-only so prompt edits take effect with
`docker compose restart` — no rebuild needed. Ollama's model cache lives in
the named volume `ollama_data`, Whisper's in `whisper_data`, and the
`remember`/`recall` memory file in `memory_data`, all surviving `down`/`up`
but not `down -v`.
