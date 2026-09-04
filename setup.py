#!/usr/bin/env python3
"""Interactive wizard to configure a new agent from this template.

Usage:
    python setup.py

Asks only for the values that make sense to customize per agent, writes the
result to .env (keeping every other key at its .env.example default),
creates app/prompts/system_prompt.txt from its template on first run, and
optionally starts the agent with `docker compose up -d --build` (pulling the
Ollama model automatically when that's the chosen backend).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"
SYSTEM_PROMPT_EXAMPLE = ROOT / "app" / "prompts" / "system_prompt.txt.example"
SYSTEM_PROMPT_FILE = ROOT / "app" / "prompts" / "system_prompt.txt"

# Keys always asked, regardless of LLM backend. SYSTEM_PROMPT_FILE, the
# *_BASE_URL keys, etc. are intentionally not here: they're internal wiring,
# not something a new agent's owner should be typing free text into.
BASE_KEYS = ["TELEGRAM_BOT_TOKEN", "ALLOWED_USER_IDS", "AGENT_NAME"]

# Extra keys asked only for the chosen backend.
BACKEND_KEYS = {
    "ollama": ["OLLAMA_MODEL"],
    "cloud": ["CLOUD_API_KEY", "CLOUD_MODEL"],
}

LLM_BACKENDS = ("ollama", "cloud")

# What people naturally type for each backend. Both sides of ask_llm_backend
# always resolve to the canonical "ollama"/"cloud" values that .env and
# app/config.py expect.
LLM_BACKEND_ALIASES = {
    "local": "ollama",
    "ollama": "ollama",
    "cloud": "cloud",
    "api": "cloud",
    "remote": "cloud",
}

PROMPTS = {
    "TELEGRAM_BOT_TOKEN": "Telegram bot token (from @BotFather)",
    "ALLOWED_USER_IDS": "Telegram IDs allowed to use the bot, comma-separated (empty = anyone)",
    "AGENT_NAME": "Agent name",
    "OLLAMA_MODEL": "Ollama model",
    "CLOUD_API_KEY": "Cloud backend API key",
    "CLOUD_MODEL": "Cloud backend model",
}

LINE_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)=(.*)$")


def parse_env_example() -> list[tuple[str, str]]:
    entries = []
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        match = LINE_RE.match(line)
        if match:
            entries.append((match.group(1), match.group(2)))
    return entries


def ask(key: str, default: str) -> str:
    label = PROMPTS.get(key, key)
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def ask_llm_backend(default: str) -> str:
    default = default if default in LLM_BACKENDS else "ollama"
    default_word = "local" if default == "ollama" else "cloud"
    while True:
        raw = input(
            f"LLM backend — type 'local' (a model running on your machine via "
            f"Ollama) or 'cloud' (an API key, e.g. OpenAI) [{default_word}]: "
        ).strip().lower()
        backend = LLM_BACKEND_ALIASES.get(raw or default_word)
        if backend:
            return backend
        print(f"Please type 'local' or 'cloud' (got {raw!r}).")


def ensure_system_prompt() -> None:
    """Create system_prompt.txt from its template on first run only.

    system_prompt.txt is gitignored on purpose: once you've personalized an
    agent, pulling updates from the template repo must not overwrite it.
    """
    if not SYSTEM_PROMPT_FILE.exists() and SYSTEM_PROMPT_EXAMPLE.exists():
        SYSTEM_PROMPT_FILE.write_text(
            SYSTEM_PROMPT_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8"
        )


def apply_personality(instructions: str) -> None:
    if instructions and SYSTEM_PROMPT_FILE.exists():
        with SYSTEM_PROMPT_FILE.open("a", encoding="utf-8") as f:
            f.write(f"\n{instructions}\n")


def pull_ollama_model(model: str, *, retries: int = 10, delay_seconds: float = 3) -> bool:
    """Download `model` into the ollama service's volume.

    The ollama container needs a moment to start accepting commands after
    `docker compose up`, so this retries a few times before giving up.
    """
    print(f"\nPulling Ollama model '{model}' (first time only, can take a while)...")
    for _ in range(retries):
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "ollama", "ollama", "pull", model],
            cwd=ROOT,
            check=False,
        )
        if result.returncode == 0:
            return True
        time.sleep(delay_seconds)

    print(
        "Could not pull the model automatically. Once the agent is up, run:\n"
        f"  docker compose exec ollama ollama pull {model}"
    )
    return False


def main() -> None:
    if ENV_FILE.exists():
        overwrite = input(".env already exists. Overwrite it? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Cancelled. Edit .env by hand if you want to change something.")
            return

    print("== Agent configuration ==\n")
    values = dict(parse_env_example())

    for key in BASE_KEYS:
        values[key] = ask(key, values.get(key, ""))

    values["LLM_BACKEND"] = ask_llm_backend(values.get("LLM_BACKEND", "ollama"))
    for key in BACKEND_KEYS[values["LLM_BACKEND"]]:
        values[key] = ask(key, values.get(key, ""))

    with ENV_FILE.open("w", encoding="utf-8") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")

    ensure_system_prompt()
    personality = input(
        "\nOptional: extra personality/instructions for the agent (leave empty to skip): "
    ).strip()
    apply_personality(personality)

    print(f"\nDone. Configuration saved to {ENV_FILE}.")

    if shutil.which("docker") is None:
        print("Docker was not found on PATH. Install Docker Desktop and then run:")
        print("  docker compose up -d --build")
        return

    launch = input("\nStart the agent now with docker compose? (Y/n): ").strip().lower()
    if launch in ("", "y"):
        subprocess.run(["docker", "compose", "up", "-d", "--build"], cwd=ROOT, check=False)
        if values["LLM_BACKEND"] == "ollama":
            pull_ollama_model(values["OLLAMA_MODEL"])
        print("\nAgent is up. Check logs with: docker compose logs -f")
    else:
        print("When you're ready: docker compose up -d --build")


def _cli() -> int:
    try:
        main()
        return 0
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(_cli())
