#!/usr/bin/env python3
"""One-command updater for an already-created agent.

Usage:
    python update.py

Equivalent to running, in order:
    git remote add template <TEMPLATE_URL>   (only the first time)
    git fetch template
    git merge template/main --no-edit
    (fill in any new .env settings the update introduced, using their
     .env.example defaults — never touches a setting you already have)
    docker compose up -d --build

Safe to re-run any time you want to check for template updates.
"""
from __future__ import annotations

import subprocess
import sys

import setup

TEMPLATE_URL = "https://github.com/salogelTorres/lak.git"
TEMPLATE_REMOTE = "template"


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(args)}")
    return subprocess.run(args, cwd=setup.ROOT, **kwargs)


def ensure_template_remote() -> None:
    result = run(["git", "remote"], capture_output=True, text=True, check=False)
    remotes = (result.stdout or "").split()
    if TEMPLATE_REMOTE not in remotes:
        run(["git", "remote", "add", TEMPLATE_REMOTE, TEMPLATE_URL], check=False)


def fetch_and_merge() -> bool:
    fetch = run(["git", "fetch", TEMPLATE_REMOTE], check=False)
    if fetch.returncode != 0:
        print("\nCould not fetch from the template repo. Check your network/remote and try again.")
        return False

    merge = run(["git", "merge", f"{TEMPLATE_REMOTE}/main", "--no-edit"], check=False)
    if merge.returncode != 0:
        print(
            "\nMerge conflict (or other git error) while pulling template updates.\n"
            "Resolve it by hand (`git status` shows the conflicting files), commit, "
            "then re-run this script."
        )
        return False
    return True


def fill_in_new_env_keys() -> list[str]:
    """A template update can introduce a new .env.example setting (e.g. a new
    feature's config). Appends any such key to .env with its example
    default so it's never silently unset; never touches a key you already
    have, even to reorder it.
    """
    if not setup.ENV_FILE.exists():
        return []

    existing_keys = {
        line.split("=", 1)[0]
        for line in setup.ENV_FILE.read_text(encoding="utf-8").splitlines()
        if "=" in line
    }

    added = []
    with setup.ENV_FILE.open("a", encoding="utf-8") as f:
        for key, default in setup.parse_env_example():
            if key not in existing_keys:
                f.write(f"{key}={default}\n")
                added.append(key)
    return added


def main() -> int:
    if not (setup.ROOT / ".git").exists():
        print("This doesn't look like a git repository (no .git folder here).")
        return 1

    ensure_template_remote()

    print("Fetching template updates...")
    if not fetch_and_merge():
        return 1

    added_keys = fill_in_new_env_keys()
    if added_keys:
        print(f"\nNew .env setting(s) added with their defaults: {', '.join(added_keys)}")
        print("Review .env and adjust if needed.")

    setup.ensure_system_prompt()
    if setup.ensure_gpu_override():
        print("NVIDIA GPU detected — enabling GPU acceleration for Ollama.")

    print("\nRebuilding with docker compose up -d --build...")
    run(["docker", "compose", "up", "-d", "--build"], check=False)
    print("\nDone. Check logs with: docker compose logs -f")
    return 0


def _cli() -> int:
    try:
        return main()
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(_cli())
