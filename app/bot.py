from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def _build_system_message(config: Config) -> dict[str, str]:
    """Recomputed on every message so the date/time is never stale, unlike
    the rest of the system prompt, which is fixed for the process lifetime.
    """
    tz_name = config.timezone
    try:
        now = datetime.now(ZoneInfo(tz_name))
    except ZoneInfoNotFoundError:
        tz_name = "UTC"
        now = datetime.now(ZoneInfo(tz_name))
    datetime_line = f"Current date and time: {now.strftime('%A, %Y-%m-%d %H:%M')} ({tz_name})"
    return {"role": "system", "content": f"{config.system_prompt}\n\n{datetime_line}"}


async def _warm_up_ollama(llm_client: LLMClient, *, retries: int = 10, delay_seconds: float = 3) -> None:
    """Load the model into memory/VRAM right away on startup.

    Otherwise the *first* real message after a fresh `docker compose up` (or
    any restart) is the one that pays the cold-load cost — which for a
    several-GB model can be a minute or more on top of generation time.
    Runs as a fire-and-forget background task; if it fails, the bot still
    works, just slow on that first message like before.

    Retries because Compose starts the bot and ollama containers together —
    the ollama service can still be a few seconds from accepting connections
    when this first fires.
    """
    for attempt in range(retries):
        try:
            await llm_client.chat([{"role": "user", "content": "Hi"}])
            logger.info("Model warmed up.")
            return
        except Exception:
            if attempt == retries - 1:
                logger.warning("Model warm-up failed; the first reply may be slow.", exc_info=True)
                return
            await asyncio.sleep(delay_seconds)


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

        history = histories.setdefault(chat_id, [None])
        history[0] = _build_system_message(config)
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

    async def post_init(application: Application) -> None:
        if config.llm_backend == "ollama":
            asyncio.create_task(_warm_up_ollama(llm_client))

    app = Application.builder().token(config.telegram_token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
