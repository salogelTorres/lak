# Telegram + LLM agent template

Template for spinning up, with a single command, a Telegram bot connected to
an LLM (local via Ollama, or remote via any OpenAI-compatible API: OpenAI,
OpenRouter, proxies, etc.), running in Docker.

## What's included

- **Docker**: `Dockerfile` + `docker-compose.yml`, with a `bot` service and,
  fully containerized, an `ollama` service — no local Ollama install needed.
- **Telegram**: `app/bot.py`, built on `python-telegram-bot`, with in-memory
  per-chat conversation history and an optional user whitelist
  (`ALLOWED_USER_IDS`).
- **Voice messages**: Telegram voice notes (and audio files) are transcribed
  locally with `faster-whisper` (CPU, no API key, independent of
  `LLM_BACKEND`) and fed to the model tagged as
  `[Voice message, transcribed by Whisper]: ...`, so it always knows a
  message was spoken rather than typed.
- **Swappable LLM backend** (`app/llm.py`): `LLM_BACKEND=ollama` (the
  `ollama` container, reached at `http://ollama:11434`) or
  `LLM_BACKEND=cloud` (any OpenAI-compatible `/chat/completions` endpoint +
  API key).
- **Prompt / personality**: `app/prompts/system_prompt.txt`, generated on
  first run from `system_prompt.txt.example`, editable without rebuilding
  the image (`docker compose restart` picks it up).
- **`setup.py`**: interactive wizard (stdlib only, no dependencies needed to
  run it) that asks for the bot token, backend, model, etc., writes `.env`
  and `system_prompt.txt`, enables NVIDIA GPU acceleration for Ollama
  automatically if it detects one, starts everything with
  `docker compose up -d --build`, and — for the `ollama` backend — pulls the
  chosen model into the `ollama` container.
- **Test suite**: `pytest` + `pytest-cov`, 99%+ line/branch coverage, no
  network or Docker required to run it (see [Running the tests](#running-the-tests)).

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker
  Engine + Compose plugin on Linux) running.
- Python 3 available on the host, only to run `setup.py` (the bot and, for
  the `ollama` backend, the model server both run inside containers).
- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- If you plan to use `LLM_BACKEND=ollama`: enough disk space and RAM for the
  model you pick (a few GB for a small model) — it downloads into the
  `ollama` container on first run, no local Ollama install required. Runs on
  CPU by default; if you have an NVIDIA GPU with the
  [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
  installed (check with `docker info | grep nvidia` — Docker Desktop with
  WSL2 sets this up for you), `setup.py` detects it and enables GPU
  acceleration automatically. A CPU-only 8B model can take 20-30+ seconds
  per reply; the same model on GPU is typically well under a second per
  token. Loading the model into memory the first time (after
  `docker compose up`, or once it's unloaded) is a separate, one-off cost
  on top of that — a few GB model can take a minute or more just to load.
  The bot warms the model up on startup so that cost lands during container
  startup rather than on the first Telegram message, and
  `OLLAMA_KEEP_ALIVE=-1` (set in `docker-compose.yml`) keeps it loaded
  indefinitely afterwards instead of Ollama's default 5-minute idle
  timeout — so in practice only a fresh `docker compose up`/restart pays
  it, not every conversation after a quiet period.
- If you plan to use `LLM_BACKEND=cloud`: an API key for an OpenAI-compatible
  provider (OpenAI, OpenRouter, etc.).
- Voice messages work regardless of `LLM_BACKEND`: the `small` Whisper model
  (default) downloads once (~500MB) into the `whisper_data` volume the first
  time you send a voice note, then runs on CPU — a few seconds for a short
  message.

## Create a new agent

1. Clone this repo under the new agent's name:

   ```bash
   git clone https://github.com/salogelTorres/lak.git my-agent
   cd my-agent
   ```

2. Run the setup wizard:

   ```bash
   python setup.py
   ```

   It asks for the Telegram token, the LLM backend (`local` for Ollama, or
   `cloud`), the model, and the API key if needed. It writes `.env`, creates
   `app/prompts/system_prompt.txt` from its template, and, if you confirm,
   builds and starts the containers with `docker compose up -d --build` —
   pulling the Ollama model automatically if you picked `local` (this can
   take a few minutes the first time, depending on model size).

3. Or configure it by hand instead:

   ```bash
   cp .env.example .env                                            # edit with your own values
   cp app/prompts/system_prompt.txt.example app/prompts/system_prompt.txt
   docker compose up -d --build
   ```

4. Open Telegram, find your bot, and send `/start`.

## Customizing the agent

- **Name and personality**: edit `app/prompts/system_prompt.txt` (supports
  the `{{AGENT_NAME}}` placeholder, filled in from `AGENT_NAME` in `.env`).
  No rebuild needed — the file is mounted as a volume, so
  `docker compose restart` is enough to pick up changes.
- **LLM backend**: `LLM_BACKEND` in `.env`, either `ollama` or `cloud`.
  - `ollama`: uses the `ollama` service from `docker-compose.yml`
    (`OLLAMA_BASE_URL=http://ollama:11434`, its default). Pull additional
    models into it any time with
    `docker compose exec ollama ollama pull <model>`.
  - `cloud`: any API exposing an OpenAI-compatible `/chat/completions`
    endpoint (OpenAI, OpenRouter, etc.). Configure `CLOUD_API_BASE_URL`,
    `CLOUD_API_KEY`, and `CLOUD_MODEL`.
- **GPU acceleration**: `docker-compose.override.yml`, generated by
  `setup.py` when it detects an NVIDIA GPU (see Requirements above), adds
  the device reservation for the `ollama` service — Compose merges it
  automatically, no extra flags on any `docker compose` command. It's
  gitignored (host-specific), so re-running `setup.py` on a machine without
  a GPU won't create one, and deleting the file reverts to CPU. To add it
  by hand: `cp docker-compose.override.yml.example docker-compose.override.yml`.
- **Access control**: `ALLOWED_USER_IDS` in `.env` restricts who can talk to
  the bot (comma-separated numeric Telegram user IDs). Empty = anyone.
- **Date/time awareness**: `TZ` in `.env` (IANA name, e.g. `Europe/Madrid`,
  default `UTC`) is what the agent is told the current date and time are.
  It's recomputed on every message (never baked in once and left to go
  stale), correctly handling DST — get this right or the model will
  confidently tell you the wrong time.
- **Voice messages**: `WHISPER_MODEL` in `.env` (`tiny`/`base`/`small`/
  `medium`/`large-v3`) trades off speed for accuracy — `small` is a
  reasonable default on CPU. Every transcription is prefixed with
  `[Voice message, transcribed by Whisper]:` before being sent to the
  model, so it can tell text and voice messages apart.

`.env`, `app/prompts/system_prompt.txt`, and `docker-compose.override.yml`
are all gitignored — see
[Updating an already-created agent](#updating-an-already-created-agent) for
why that matters.

## Running multiple agents

Each agent is an independent clone/folder with its own `.env`, its own
`system_prompt.txt`, and its own `docker-compose` stack. To create another
one, repeat the "Create a new agent" steps in a different folder with a
different Telegram token.

## Updating an already-created agent

Every agent is a separate clone of this repo, so improvements you push here
(new features, bug fixes, a new LLM backend) don't reach existing agents by
themselves — each clone has to pull them. Because the files that hold
per-agent/per-host state — `.env`, `app/prompts/system_prompt.txt`, and
`docker-compose.override.yml` — are gitignored (never committed), pulling
template updates never overwrites your customization or GPU config — only
tracked files (code, `Dockerfile`, `docker-compose.yml`, the `.example`
files, etc.) get updated.

Whenever you want to pull in the latest template changes, from the agent's
folder:

```bash
python update.py
```

It adds the `template` remote the first time it's needed, then runs, in
order: `git fetch template`, `git merge template/main --no-edit`, fills in
any *new* `.env` setting the update introduced (using its `.env.example`
default — never touches a setting you already have), re-creates
`system_prompt.txt`/`docker-compose.override.yml` if they went missing,
enables GPU acceleration if this machine has one and didn't before, and
finally `docker compose up -d --build`. Safe to re-run any time.

If you've hand-edited a tracked file too (rare — normally only `.env`,
`system_prompt.txt`, and `docker-compose.override.yml` are), the merge step
will flag a conflict for that file; resolve it by hand (`git status` shows
which), commit, and run `python update.py` again. The personalization/host
files themselves are never part of the conflict since git doesn't track
them.

Equivalent by hand, if you'd rather not run the script:

```bash
git remote add template https://github.com/salogelTorres/lak.git   # once
git fetch template
git merge template/main
docker compose up -d --build
```

## Running the tests

```bash
python -m venv .venv
.venv/Scripts/activate        # on Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

`pytest` runs with coverage enabled (`pyproject.toml`) and fails the run if
line+branch coverage drops below 99%. No Docker, Telegram, or LLM backend
is required — all I/O (HTTP calls, `input()`, `subprocess`) is mocked.

## Useful commands

```bash
docker compose logs -f                            # follow logs (both services)
docker compose restart bot                         # restart the bot (e.g. after editing the prompt)
docker compose exec ollama ollama pull <model>     # pull/switch models
docker compose exec ollama ollama list             # see what's downloaded
docker compose down                                # stop and remove the containers
```

Downloaded Ollama models persist in the `ollama_data` Docker volume across
`docker compose down`/`up` — they're only re-downloaded if you remove that
volume too (`docker compose down -v`). The Whisper model works the same way,
in the `whisper_data` volume.

## Possible next steps

- Try a real end-to-end run (`docker compose up`) with an actual bot token
  and confirm replies work with both backends.
- Optionally wrap the clone step in a single script/command that does the
  `git clone` for you, taking the agent name as an argument.
