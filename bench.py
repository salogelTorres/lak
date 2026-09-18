#!/usr/bin/env python3
"""Run the THINK / NO_THINK router benchmark against one or more Ollama models.

Usage:
    python bench.py qwen3:0.6b qwen3:1.7b qwen3:4b
    python bench.py qwen3:4b -- --attempts 5 --limit 20

Pulls any listed model that isn't downloaded yet, then runs
evals/router_bench.py inside the bot container — so nothing beyond Docker
is needed on the host — and prints its report. Raw per-call results land in
evals/results/ on the host through the evals/ bind mount in
docker-compose.yml. Anything after `--` is passed through to
router_bench.py unchanged (see `python -m evals.router_bench --help`).

The agent (`docker compose up`) must already be running: the benchmark runs
in its `bot` container against its `ollama` service.
"""
from __future__ import annotations

import subprocess
import sys

from setup import ROOT, ensure_docker_running, pull_ollama_model


def parse_args(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split `model... [-- passthrough...]` into (models, passthrough)."""
    if "--" in argv:
        split = argv.index("--")
        return argv[:split], argv[split + 1 :]
    return argv, []


def installed_models() -> set[str]:
    """Model names Ollama already has, so we only pull what's missing (and
    don't need the network just to re-check a model that's already there)."""
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "ollama", "ollama", "list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    names: set[str] = set()
    for line in result.stdout.splitlines()[1:]:  # first line is the header
        parts = line.split()
        if parts:
            names.add(parts[0])
            names.add(parts[0].removesuffix(":latest"))
    return names


def main(argv: list[str] | None = None) -> int:
    models, passthrough = parse_args(sys.argv[1:] if argv is None else argv)
    if not models:
        print(__doc__)
        return 2

    if not ensure_docker_running():
        return 1

    present = installed_models()
    for model in models:
        if model not in present and not pull_ollama_model(model):
            return 1

    command = ["docker", "compose", "exec", "-T", "bot", "python", "-m", "evals.router_bench", "--models", *models]
    return subprocess.run([*command, *passthrough], cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
