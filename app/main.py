from __future__ import annotations

import logging

from app.bot import build_application
from app.config import Config
from app.llm import build_llm_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    config = Config.load()
    llm_client = build_llm_client(config)
    app = build_application(config, llm_client)
    logging.info("Starting %s (backend=%s)", config.agent_name, config.llm_backend)
    app.run_polling()


if __name__ == "__main__":
    main()
