#!/usr/bin/env python3
"""Asistente interactivo para configurar un nuevo agente a partir de esta plantilla.

Uso:
    python setup.py

Lee .env.example, pregunta valor por valor (con el valor por defecto entre
corchetes), escribe el resultado en .env y, si quieres, levanta el agente
con `docker compose up -d --build`.
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

PROMPTS = {
    "TELEGRAM_BOT_TOKEN": "Token del bot de Telegram (de @BotFather)",
    "ALLOWED_USER_IDS": "IDs de Telegram con acceso, separados por comas (vacío = cualquiera)",
    "AGENT_NAME": "Nombre del agente",
    "LLM_BACKEND": "Backend del LLM: 'ollama' (local) o 'cloud' (API con key)",
    "OLLAMA_BASE_URL": "URL de Ollama",
    "OLLAMA_MODEL": "Modelo de Ollama",
    "CLOUD_API_BASE_URL": "URL base de la API cloud (OpenAI-compatible)",
    "CLOUD_API_KEY": "API key del backend cloud",
    "CLOUD_MODEL": "Modelo del backend cloud",
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


def main() -> None:
    if ENV_FILE.exists():
        overwrite = input(".env ya existe. ¿Sobreescribirlo? (s/N): ").strip().lower()
        if overwrite != "s":
            print("Cancelado. Edita .env a mano si quieres cambiar algo.")
            return

    print("== Configuración del agente ==\n")
    values: dict[str, str] = {}
    for key, default in parse_env_example():
        values[key] = ask(key, default)

    with ENV_FILE.open("w", encoding="utf-8") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")

    print(f"\nListo. Configuración guardada en {ENV_FILE}.")

    if shutil.which("docker") is None:
        print("No se encontró Docker en el PATH. Instala Docker Desktop y luego ejecuta:")
        print("  docker compose up -d --build")
        return

    launch = input("\n¿Levantar el agente ahora con docker compose? (S/n): ").strip().lower()
    if launch in ("", "s"):
        subprocess.run(["docker", "compose", "up", "-d", "--build"], cwd=ROOT, check=False)
        print("\nAgente en marcha. Revisa los logs con: docker compose logs -f")
    else:
        print("Cuando quieras arrancarlo: docker compose up -d --build")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
