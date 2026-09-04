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
- `llm.py` — `LLMClient` Protocol with `OllamaClient` and `CloudClient`
  (any OpenAI-compatible `/chat/completions` endpoint); `build_llm_client()`
  picks one from `Config.llm_backend`. Both are thin `httpx` wrappers with no
  retry/streaming logic.
- `bot.py` — `build_application()` wires `python-telegram-bot` handlers.
  Conversation history is an in-memory `dict[chat_id, list[message]]` closed
  over inside `build_application` (lost on restart, capped at
  `MAX_HISTORY_MESSAGES`), not a module-level or persisted store. `handle_message`
  (text) and `handle_voice` (voice notes/audio files) both funnel through the
  shared `_reply_to()` closure (access control, history, typing indicator,
  LLM call, error handling, trimming) — add new input types the same way
  rather than duplicating that logic. Voice notes are transcribed with
  `faster-whisper` (`_transcribe_sync`, run off the event loop via
  `asyncio.to_thread` since it's a blocking CPU call) and always prefixed
  with `VOICE_TRANSCRIPTION_PREFIX` before being added to history, so the
  model can tell a message was spoken vs. typed — the system prompt template
  explains the convention. The `WhisperModel` instance is cached per model
  name in the module-level `_whisper_models` dict (loading one is slow), not
  reloaded per message.

**Docker**: `docker-compose.yml` defines `bot` and `ollama` as separate
services on the Compose network; the bot always reaches Ollama at
`http://ollama:11434` regardless of backend choice (the `ollama` service
just sits idle if `LLM_BACKEND=cloud`). `app/prompts/` is bind-mounted into
the container read-only so prompt edits take effect with
`docker compose restart` — no rebuild needed. Ollama's model cache lives in
the named volume `ollama_data`, and Whisper's in `whisper_data`, both
surviving `down`/`up` but not `down -v`.
