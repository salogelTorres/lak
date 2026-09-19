from __future__ import annotations

import logging

from app.bot import build_application
from app.config import Config
from app.llm import build_llm_client
from app.router import OllamaRouter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    config = Config.load()
    llm_client = build_llm_client(config)
    # Ollama-only: no equivalent `think` flag exists to gate on any other
    # backend, and ROUTER_MODEL is empty by default (disabled) either way.
    router = (
        OllamaRouter(config.ollama_base_url, config.router_model)
        if config.llm_backend == "ollama" and config.router_model
        else None
    )
    app = build_application(config, llm_client, router)
    logging.info("Starting %s (backend=%s)", config.agent_name, config.llm_backend)
    app.run_polling()


if __name__ == "__main__":
    main()
