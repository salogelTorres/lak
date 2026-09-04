from __future__ import annotations

import asyncio
import contextlib
import io
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from faster_whisper import WhisperModel
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

from app.config import Config
from app.llm import LLMClient

logger = logging.getLogger(__name__)

TYPING_REFRESH_SECONDS = 4

# Rough rule of thumb for BPE tokenizers (OpenAI's own guidance for
# English/Spanish): ~4 characters per token. Real tokenizers differ per
# model, but we only need a consistent budget to keep history within the
# model's context window, not exact accounting.
CHARS_PER_TOKEN_ESTIMATE = 4

# Prepended to every voice-note transcription so the model can always tell a
# message was spoken rather than typed — otherwise "listen to that audio I
# sent" is meaningless to it, since it only ever sees text.
VOICE_TRANSCRIPTION_PREFIX = "[Voice message, transcribed by Whisper]"

WHISPER_DOWNLOAD_ROOT = "/data/whisper"

_whisper_models: dict[str, WhisperModel] = {}


def _is_allowed(config: Config, user_id: int) -> bool:
    return not config.allowed_user_ids or user_id in config.allowed_user_ids


def _get_whisper_model(model_name: str) -> WhisperModel:
    # Loading a model is slow (first run downloads it too), so cache one
    # instance per model name for the life of the process instead of
    # reloading it on every voice message.
    if model_name not in _whisper_models:
        _whisper_models[model_name] = WhisperModel(
            model_name, device="cpu", compute_type="int8", download_root=WHISPER_DOWNLOAD_ROOT
        )
    return _whisper_models[model_name]


def _transcribe_sync(audio_bytes: bytes, model_name: str) -> str:
    model = _get_whisper_model(model_name)
    segments, _info = model.transcribe(io.BytesIO(audio_bytes))
    return " ".join(segment.text.strip() for segment in segments).strip()


async def transcribe_voice(audio_bytes: bytes, model_name: str) -> str:
    # faster-whisper is a blocking, CPU-bound call — run it off the event
    # loop so it doesn't freeze the bot (typing indicators, other chats)
    # while it works.
    return await asyncio.to_thread(_transcribe_sync, audio_bytes, model_name)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN_ESTIMATE)


def _trim_to_token_budget(history: list[dict[str, str]], max_tokens: int) -> list[dict[str, str]]:
    """Keep the system message (index 0) and as much of the *most recent*
    history as fits in max_tokens, dropping the oldest messages first —
    regardless of how many messages that ends up being.

    The newest message (the current turn) is always kept even if it alone
    exceeds the budget: better to slightly overrun than to silently drop
    the question the user just asked.
    """
    system_message = history[0]
    rest = history[1:]
    if not rest:
        return [system_message]

    budget = max_tokens - _estimate_tokens(system_message["content"])
    newest = rest[-1]
    kept = [newest]
    budget -= _estimate_tokens(newest["content"])

    for message in reversed(rest[:-1]):
        cost = _estimate_tokens(message["content"])
        if cost > budget:
            break
        kept.append(message)
        budget -= cost

    kept.reverse()
    return [system_message, *kept]


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

    async def _has_access(update: Update) -> bool:
        user = update.effective_user
        if user is None or not _is_allowed(config, user.id):
            await update.message.reply_text("You don't have access to this bot.")
            return False
        return True

    async def _reply_to(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        chat_id = update.effective_chat.id
        history = histories.setdefault(chat_id, [None])
        history[0] = _build_system_message(config)
        history.append({"role": "user", "content": text})
        # bound what we're about to send *before* sending it, not after —
        # trims oldest messages first, whatever number of them that is
        history = _trim_to_token_budget(history, config.max_history_tokens)
        histories[chat_id] = history

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
        await update.message.reply_text(reply)

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _has_access(update):
            return
        await _reply_to(update, context, update.message.text)

    async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _has_access(update):
            return

        voice = update.message.voice or update.message.audio
        telegram_file = await context.bot.get_file(voice.file_id)
        audio_bytes = bytes(await telegram_file.download_as_bytearray())

        try:
            text = await transcribe_voice(audio_bytes, config.whisper_model)
        except Exception:
            logger.exception("Failed transcribing voice message")
            await update.message.reply_text(
                "Couldn't transcribe that voice message. Please try again or send it as text."
            )
            return

        text = text.strip()
        if not text:
            await update.message.reply_text("I couldn't make out any speech in that voice message.")
            return

        await _reply_to(update, context, f"{VOICE_TRANSCRIPTION_PREFIX}: {text}")

    async def post_init(application: Application) -> None:
        if config.llm_backend == "ollama":
            # asyncio only keeps a *weak* reference to a task once nothing
            # else holds it, so an unstored fire-and-forget task can be
            # garbage-collected mid-run (see the asyncio.create_task docs).
            # Stash it on bot_data so it's guaranteed to run to completion.
            application.bot_data["warm_up_task"] = asyncio.create_task(_warm_up_ollama(llm_client))

    app = Application.builder().token(config.telegram_token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
