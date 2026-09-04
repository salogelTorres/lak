#!/usr/bin/env python3
"""Interactive wizard to configure a new agent from this template.

Usage:
    python setup.py

Reads .env.example, asks for each value (showing the default in brackets),
writes the result to .env, creates app/prompts/system_prompt.txt from its
template on first run, and optionally starts the agent with
`docker compose up -d --build`.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"
SYSTEM_PROMPT_EXAMPLE = ROOT / "app" / "prompts" / "system_prompt.txt.example"
SYSTEM_PROMPT_FILE = ROOT / "app" / "prompts" / "system_prompt.txt"

PROMPTS = {
    "TELEGRAM_BOT_TOKEN": "Telegram bot token (from @BotFather)",
    "ALLOWED_USER_IDS": "Telegram IDs allowed to use the bot, comma-separated (empty = anyone)",
    "AGENT_NAME": "Agent name",
    "LLM_BACKEND": "LLM backend: 'ollama' (local) or 'cloud' (API with key)",
    "OLLAMA_BASE_URL": "Ollama URL",
    "OLLAMA_MODEL": "Ollama model",
    "CLOUD_API_BASE_URL": "Cloud API base URL (OpenAI-compatible)",
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


def ensure_system_prompt() -> None:
    """Create system_prompt.txt from its template on first run only.

    system_prompt.txt is gitignored on purpose: once you've personalized an
    agent, pulling updates from the template repo must not overwrite it.
    """
    if not SYSTEM_PROMPT_FILE.exists() and SYSTEM_PROMPT_EXAMPLE.exists():
        SYSTEM_PROMPT_FILE.write_text(
            SYSTEM_PROMPT_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8"
        )


def main() -> None:
    if ENV_FILE.exists():
        overwrite = input(".env already exists. Overwrite it? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Cancelled. Edit .env by hand if you want to change something.")
            return

    print("== Agent configuration ==\n")
    values: dict[str, str] = {}
    for key, default in parse_env_example():
        values[key] = ask(key, default)

    with ENV_FILE.open("w", encoding="utf-8") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")

    ensure_system_prompt()

    print(f"\nDone. Configuration saved to {ENV_FILE}.")

    if shutil.which("docker") is None:
        print("Docker was not found on PATH. Install Docker Desktop and then run:")
        print("  docker compose up -d --build")
        return

    launch = input("\nStart the agent now with docker compose? (Y/n): ").strip().lower()
    if launch in ("", "y"):
        subprocess.run(["docker", "compose", "up", "-d", "--build"], cwd=ROOT, check=False)
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
