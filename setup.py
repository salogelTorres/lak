#!/usr/bin/env python3
"""Interactive wizard to configure a new agent from this template.

Usage:
    python setup.py

Asks only for the values that make sense to customize per agent, writes the
result to .env (keeping every other key at its .env.example default),
creates app/prompts/system_prompt.txt from its template on first run, enables
NVIDIA GPU acceleration for Ollama automatically when one is detected, and
optionally starts the agent with `docker compose up -d --build` (pulling the
Ollama model automatically when that's the chosen backend).
"""
from __future__ import annotations

import platform
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
GPU_OVERRIDE_EXAMPLE = ROOT / "docker-compose.override.yml.example"
GPU_OVERRIDE_FILE = ROOT / "docker-compose.override.yml"

# Keys always asked, regardless of LLM backend. SYSTEM_PROMPT_FILE, the
# *_BASE_URL keys, etc. are intentionally not here: they're internal wiring,
# not something a new agent's owner should be typing free text into.
BASE_KEYS = ["TELEGRAM_BOT_TOKEN", "ALLOWED_USER_IDS", "AGENT_NAME", "TZ"]

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

# Tools an agent can opt into via ENABLED_TOOLS, mirrored here (name ->
# description) rather than imported from app.tools, so setup.py stays
# stdlib-only and runnable before the app's dependencies are installed.
# Keep in sync with app/tools/__init__.py's AVAILABLE_TOOLS catalog.
AVAILABLE_TOOLS = {
    "search_web": "DuckDuckGo web search, no API key needed",
    "fetch_page": "Fetch a specific web page and read its full text (deeper research alongside search_web)",
    "remember": "Save a note to persistent memory for a chat (survives restarts)",
    "recall": "Retrieve everything remembered for a chat (pairs with remember)",
    "get_weather": "Current weather for a place, via Open-Meteo, no API key needed",
    "remind_me": "Schedule a reminder message to be sent back to a chat later",
    "think_harder": "Re-answer the current question with extended reasoning (Ollama + e.g. qwen3 only)",
}

PROMPTS = {
    "TELEGRAM_BOT_TOKEN": "Telegram bot token (from @BotFather)",
    "ALLOWED_USER_IDS": "Telegram IDs allowed to use the bot, comma-separated (empty = anyone)",
    "AGENT_NAME": "Agent name",
    "TZ": "Timezone (IANA name, e.g. Europe/Madrid, America/New_York)",
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


def ask_enabled_tools(default: str) -> str:
    """Which tools (if any) the agent may call mid-conversation. Requires a
    model that supports tool calling; unknown/typo'd names are dropped
    silently, same as resolve_tools() does for the running agent."""
    print("\nAvailable tools (needs a model that supports tool calling):")
    for name, description in AVAILABLE_TOOLS.items():
        print(f"  {name} — {description}")
    raw = input(
        f"Enable which tools? (comma-separated names, empty = none) [{default}]: "
    ).strip()
    chosen = raw or default
    return ",".join(name for name in (n.strip() for n in chosen.split(",")) if name in AVAILABLE_TOOLS)


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


def detect_nvidia_gpu() -> bool:
    """Best-effort check for a usable NVIDIA GPU + driver on the host."""
    return shutil.which("nvidia-smi") is not None


def ensure_gpu_override() -> bool:
    """Enable GPU acceleration for the ollama service if an NVIDIA GPU is
    detected. Never overwrites a docker-compose.override.yml you already
    have (hand-edited or from a previous run). Returns whether it created
    one just now.
    """
    if GPU_OVERRIDE_FILE.exists() or not detect_nvidia_gpu() or not GPU_OVERRIDE_EXAMPLE.exists():
        return False
    GPU_OVERRIDE_FILE.write_text(
        GPU_OVERRIDE_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return True


def docker_is_running() -> bool:
    result = subprocess.run(
        ["docker", "info"], capture_output=True, check=False,
    )
    return result.returncode == 0


def _start_docker_daemon() -> bool:
    """Best-effort attempt to launch the Docker daemon/Desktop app for the
    current OS. Returns whether a launch was attempted (not whether it
    succeeded — caller polls docker_is_running() for that).
    """
    system = platform.system()

    if system == "Windows":
        for candidate in (
            Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe"),
            Path.home() / r"AppData\Local\Programs\Docker\Docker\Docker Desktop.exe",
        ):
            if candidate.exists():
                subprocess.Popen([str(candidate)], close_fds=True)
                return True
        return False

    if system == "Darwin":
        if shutil.which("open") is None:
            return False
        subprocess.run(["open", "-a", "Docker"], check=False)
        return True

    if system == "Linux":
        if shutil.which("systemctl") is not None:
            result = subprocess.run(
                ["systemctl", "start", "docker"], capture_output=True, check=False
            )
            if result.returncode == 0:
                return True
        if shutil.which("service") is not None:
            result = subprocess.run(
                ["service", "docker", "start"], capture_output=True, check=False
            )
            return result.returncode == 0
        return False

    return False


def ensure_docker_running(*, timeout_seconds: int = 90, poll_seconds: float = 3) -> bool:
    """Make sure the Docker daemon is up before `docker compose` is invoked.

    Docker Desktop/daemon startup can take anywhere from a few seconds to
    over a minute, so this launches it (if not already running) and polls
    until it responds or `timeout_seconds` elapses.
    """
    if docker_is_running():
        return True

    print("Docker is not running — attempting to start it...")
    if not _start_docker_daemon():
        print(
            "Could not start Docker automatically. Start Docker Desktop (or the "
            "docker service) yourself and re-run this command."
        )
        return False

    waited = 0.0
    while waited < timeout_seconds:
        time.sleep(poll_seconds)
        waited += poll_seconds
        if docker_is_running():
            print("Docker is up.")
            return True

    print(
        f"Docker did not become ready within {timeout_seconds}s. "
        "Once it's up, run `docker compose up -d --build` yourself."
    )
    return False


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

    values["ENABLED_TOOLS"] = ask_enabled_tools(values.get("ENABLED_TOOLS", ""))

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

    if values["LLM_BACKEND"] == "ollama" and ensure_gpu_override():
        print("NVIDIA GPU detected — enabling GPU acceleration for Ollama.")

    launch = input("\nStart the agent now with docker compose? (Y/n): ").strip().lower()
    if launch in ("", "y"):
        if not ensure_docker_running():
            return
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
