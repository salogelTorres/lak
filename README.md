# Telegram + LLM agent template

Template for spinning up, with a single command, a Telegram bot connected to
an LLM (local via Ollama, or remote via any OpenAI-compatible API: OpenAI,
OpenRouter, proxies, etc.), running in Docker.

## What's included

- **Docker**: `Dockerfile` + `docker-compose.yml`, single `bot` service.
- **Telegram**: `app/bot.py`, built on `python-telegram-bot`, with in-memory
  per-chat conversation history and an optional user whitelist
  (`ALLOWED_USER_IDS`).
- **Swappable LLM backend** (`app/llm.py`): `LLM_BACKEND=ollama` (local
  model, reached at `host.docker.internal:11434`) or `LLM_BACKEND=cloud`
  (any OpenAI-compatible `/chat/completions` endpoint + API key).
- **Prompt / personality**: `app/prompts/system_prompt.txt`, generated on
  first run from `system_prompt.txt.example`, editable without rebuilding
  the image (`docker compose restart` picks it up).
- **`setup.py`**: interactive wizard (stdlib only, no dependencies needed to
  run it) that asks for the bot token, backend, model, etc., writes `.env`
  and `system_prompt.txt`, and optionally runs `docker compose up -d --build`
  for you.
- **Test suite**: `pytest` + `pytest-cov`, 99%+ line/branch coverage, no
  network or Docker required to run it (see [Running the tests](#running-the-tests)).

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker
  Engine + Compose plugin on Linux) running.
- Python 3 available on the host, only to run `setup.py` (the bot itself runs
  inside the container).
- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- If you plan to use `LLM_BACKEND=ollama`: [Ollama](https://ollama.com)
  installed and running on the host, with a model pulled
  (e.g. `ollama pull llama3`).
- If you plan to use `LLM_BACKEND=cloud`: an API key for an OpenAI-compatible
  provider (OpenAI, OpenRouter, etc.).

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

   It asks for the Telegram token, the LLM backend (`ollama` or `cloud`), the
   model, and the API key if needed. It writes `.env`, creates
   `app/prompts/system_prompt.txt` from its template, and, if you confirm,
   builds and starts the container with `docker compose up -d --build`.

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
  - `ollama`: uses a local model. If Ollama runs on the host (not in
    Docker), `OLLAMA_BASE_URL=http://host.docker.internal:11434` already
    works out of the box on Docker Desktop (Windows/Mac).
  - `cloud`: any API exposing an OpenAI-compatible `/chat/completions`
    endpoint (OpenAI, OpenRouter, etc.). Configure `CLOUD_API_BASE_URL`,
    `CLOUD_API_KEY`, and `CLOUD_MODEL`.
- **Access control**: `ALLOWED_USER_IDS` in `.env` restricts who can talk to
  the bot (comma-separated numeric Telegram user IDs). Empty = anyone.

`.env` and `app/prompts/system_prompt.txt` are both gitignored — see
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
themselves — each clone has to pull them. Because the two files that hold
per-agent personalization, `.env` and `app/prompts/system_prompt.txt`, are
gitignored (never committed), pulling template updates never overwrites your
customization — only tracked files (code, `Dockerfile`, `docker-compose.yml`,
the `.example` files, etc.) get updated.

In each agent's folder, one-time setup:

```bash
git remote add template https://github.com/salogelTorres/lak.git
```

Whenever you want to pull in the latest template changes:

```bash
git fetch template
git merge template/main
docker compose up -d --build   # rebuild with the updated code
```

If you've hand-edited a tracked file too (rare — normally only `.env` and
`system_prompt.txt` are), git will flag a merge conflict for that file; the
personalization files themselves are never part of the conflict since git
doesn't track them.

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
docker compose logs -f      # follow logs
docker compose restart      # restart (e.g. after editing the prompt)
docker compose down         # stop and remove the container
```

## Possible next steps

- Try a real end-to-end run (`docker compose up`) with an actual bot token
  and confirm replies work with both backends.
- Optionally wrap the clone step in a single script/command that does the
  `git clone` for you, taking the agent name as an argument.
