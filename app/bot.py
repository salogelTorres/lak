from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

from app.config import Config
from app.llm import LLMClient

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20


def _is_allowed(config: Config, user_id: int) -> bool:
    return not config.allowed_user_ids or user_id in config.allowed_user_ids


def build_application(config: Config, llm_client: LLMClient) -> Application:
    # per-chat conversation history, kept in memory only (reset on restart)
    histories: dict[int, list[dict[str, str]]] = {}

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(f"Hi, I'm {config.agent_name}. How can I help?")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat_id = update.effective_chat.id

        if user is None or not _is_allowed(config, user.id):
            await update.message.reply_text("You don't have access to this bot.")
            return

        history = histories.setdefault(chat_id, [{"role": "system", "content": config.system_prompt}])
        history.append({"role": "user", "content": update.message.text})

        try:
            reply = await llm_client.chat(history)
        except Exception:
            logger.exception("Failed calling the LLM")
            await update.message.reply_text("Something went wrong talking to the model. Please try again.")
            return

        history.append({"role": "assistant", "content": reply})
        # trim history, always keeping the system prompt at index 0
        if len(history) > MAX_HISTORY_MESSAGES:
            histories[chat_id] = [history[0], *history[-(MAX_HISTORY_MESSAGES - 1):]]

        await update.message.reply_text(reply)

    app = Application.builder().token(config.telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
