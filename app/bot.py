from __future__ import annotations

import asyncio
import contextlib
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

from app.config import Config
from app.llm import LLMClient

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20
TYPING_REFRESH_SECONDS = 4


def _is_allowed(config: Config, user_id: int) -> bool:
    return not config.allowed_user_ids or user_id in config.allowed_user_ids


async def _keep_typing(bot, chat_id: int) -> None:
    """Re-send the 'typing…' indicator every few seconds.

    Telegram only shows it for ~5s per call, and a slow local model can take
    30s+ to reply, so a single send_chat_action isn't enough — this runs as
    a background task for the duration of the LLM call and gets cancelled
    once a reply is ready.
    """
    while True:
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(TYPING_REFRESH_SECONDS)


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

        typing_task = asyncio.create_task(_keep_typing(context.bot, chat_id))
        try:
            reply = await llm_client.chat(history)
        except Exception:
            logger.exception("Failed calling the LLM")
            await update.message.reply_text("Something went wrong talking to the model. Please try again.")
            return
        finally:
            typing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await typing_task

        history.append({"role": "assistant", "content": reply})
        # trim history, always keeping the system prompt at index 0
        if len(history) > MAX_HISTORY_MESSAGES:
            histories[chat_id] = [history[0], *history[-(MAX_HISTORY_MESSAGES - 1):]]

        await update.message.reply_text(reply)

    app = Application.builder().token(config.telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
