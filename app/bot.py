from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import io
import logging
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from faster_whisper import WhisperModel
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

from app.config import Config
from app.llm import LLMClient
from app.router import OllamaRouter
from app.tools import resolve_tools
from app.tools.base import ToolContext

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

COMPACTING_NOTICE = "One moment — compacting older conversation history to keep things running smoothly..."

COMPACTION_SYSTEM_PROMPT = (
    "You are compacting the history of an ongoing conversation between a user and an "
    "assistant, to save space. Write a concise summary that preserves important facts, "
    "names, decisions, and unresolved questions. Reply with the summary text only, "
    "nothing else."
)

WHISPER_DOWNLOAD_ROOT = "/data/whisper"

# Kept short so a long note/query/URL doesn't turn the heads-up itself into
# a wall of text in the chat.
_ARG_PREVIEW_LIMIT = 200


def _preview(value: Any) -> str:
    text = str(value).strip()
    return text if len(text) <= _ARG_PREVIEW_LIMIT else f"{text[:_ARG_PREVIEW_LIMIT]}…"


# Sent to the chat right before a tool actually runs, so a call that takes a
# few seconds (a web request, a file write) doesn't look like the bot has
# stalled — and *what* it's doing (the query, the URL, ...), not just that
# it's doing something. Each formatter takes the tool's parsed arguments and
# falls back to a plain label if the argument it wants isn't there. A tool
# with no entry here still gets a generic "Using {name}..." message rather
# than silence, so a new tool works without needing to touch this dict first.
TOOL_CALL_LABELS: dict[str, Callable[[dict[str, Any]], str]] = {
    "search_web": lambda args: (
        f"🔍 Searching the web for: {_preview(args['query'])}" if args.get("query") else "🔍 Searching the web..."
    ),
    "fetch_page": lambda args: (
        f"📖 Reading page: {_preview(args['url'])}" if args.get("url") else "📖 Reading a page..."
    ),
    "remember": lambda args: (
        f"💾 Saving to memory: {_preview(args['note'])}" if args.get("note") else "💾 Saving that to memory..."
    ),
    "recall": lambda args: "🧠 Checking my memory...",
    "get_weather": lambda args: (
        f"🌤️ Checking the weather in {_preview(args['location'])}..."
        if args.get("location")
        else "🌤️ Checking the weather..."
    ),
    "remind_me": lambda args: (
        f"⏰ Setting a reminder in {args['minutes']:g} min: {_preview(args['message'])}"
        if args.get("minutes") and args.get("message")
        else "⏰ Setting a reminder..."
    ),
    "think_harder": lambda args: "🤔 Thinking it through...",
}

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


def _split_recent(messages: list[dict[str, str]], recent_tokens: int) -> tuple[list[dict], list[dict]]:
    """Split messages into (older, recent): recent is the newest messages
    whose combined size fits within recent_tokens (always includes at least
    the last message), older is everything before that — candidates for
    compaction rather than being sent to the model verbatim.
    """
    if not messages:
        return [], []

    recent = [messages[-1]]
    budget = recent_tokens - _estimate_tokens(messages[-1]["content"])
    for message in reversed(messages[:-1]):
        cost = _estimate_tokens(message["content"])
        if cost > budget:
            break
        recent.append(message)
        budget -= cost

    recent.reverse()
    older = messages[: len(messages) - len(recent)]
    return older, recent


async def _compact_history(llm_client: LLMClient, existing_summary: str, messages: list[dict[str, str]]) -> str:
    """Summarize `messages` (folding in `existing_summary`, if any) into a
    single short paragraph, via the same LLM used for replies.

    Called instead of just dropping old messages once the token budget is
    exceeded, so older context isn't lost outright — just condensed.
    """
    conversation = "\n".join(f"{message['role']}: {message['content']}" for message in messages)
    user_content = (
        f"Existing summary:\n{existing_summary}\n\nNew messages to fold in:\n{conversation}"
        if existing_summary
        else conversation
    )
    reply = await llm_client.chat(
        [
            {"role": "system", "content": COMPACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
    )
    return reply.strip()


def _build_system_message(config: Config, summary: str = "") -> dict[str, str]:
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
    content = f"{config.system_prompt}\n\n{datetime_line}"
    if summary:
        content += f"\n\nSummary of earlier conversation (compacted to save space): {summary}"
    return {"role": "system", "content": content}


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


def _make_tool_context(application: Application, chat_id: int) -> ToolContext:
    """Build the per-chat context threaded into tools that declare
    `needs_context` (persistent memory, reminders) — see
    app.tools.base.ToolContext. Kept out of _reply_to itself since it needs
    nothing from that closure besides `application` and `chat_id`.
    """
    reminder_tasks: set[concurrent.futures.Future] = application.bot_data.setdefault("reminder_tasks", set())
    # _make_tool_context() itself always runs on the main loop (called
    # directly from _reply_to, never via asyncio.to_thread), so this is the
    # right loop to hand reminders back to below.
    loop = asyncio.get_running_loop()

    def schedule_reminder(delay_seconds: float, message: str) -> None:
        async def _fire() -> None:
            await asyncio.sleep(delay_seconds)
            try:
                await application.bot.send_message(chat_id, f"⏰ Reminder: {message}")
            except Exception:
                logger.exception("Failed sending reminder")

        # schedule_reminder() runs wherever the tool it backs runs — and
        # _call_tool() runs *every* tool via asyncio.to_thread, needs_context
        # or not, so this is always called from a worker thread with no
        # event loop of its own. asyncio.create_task() would raise
        # "no running event loop" there; run_coroutine_threadsafe() hands
        # the coroutine to the *main* loop captured above instead. The
        # returned Future needs the same strong-reference treatment as a
        # bare create_task() result (see _warm_up_ollama below) so it can't
        # be garbage-collected mid-sleep — held in reminder_tasks until
        # add_done_callback() removes it. Cleanup is a callback on the
        # Future rather than code inside _fire() referencing `task` by
        # closure: run_coroutine_threadsafe() schedules _fire() on another
        # thread, which could in principle start running before this
        # function returns and binds `task`, racing the closure.
        task = asyncio.run_coroutine_threadsafe(_fire(), loop)
        reminder_tasks.add(task)
        task.add_done_callback(reminder_tasks.discard)

    return ToolContext(chat_id=chat_id, schedule_reminder=schedule_reminder)


def _make_on_tool_call(update: Update):
    async def on_tool_call(name: str, arguments: dict[str, Any]) -> None:
        formatter = TOOL_CALL_LABELS.get(name)
        try:
            label = formatter(arguments) if formatter else f"🔧 Using {name}..."
        except Exception:
            # A formatter expects specific argument shapes; a model that
            # sends something unexpected (wrong type, missing key some
            # other way) must never take the whole reply down with it —
            # same "one broken tool can't break the conversation"
            # philosophy as the rest of the tool-calling machinery.
            logger.exception("Failed formatting tool-call label for %r", name)
            label = f"🔧 Using {name}..."
        await update.message.reply_text(label)

    return on_tool_call


async def _send_formatted_reply(update: Update, text: str) -> None:
    """Send the model's reply with Telegram's Markdown rendering enabled —
    models naturally write Markdown (**bold**, [text](url), etc.), and
    Telegram shows that as literal, unrendered symbols without this.

    Falls back to plain text if the reply isn't valid Markdown (an
    unbalanced `*`/`_`/`` ` `` is enough to trip Telegram's parser): a
    formatting quirk must never eat the reply outright.
    """
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except BadRequest:
        logger.warning("Reply wasn't valid Markdown; sending as plain text", exc_info=True)
        await update.message.reply_text(text)


def build_application(config: Config, llm_client: LLMClient, router: OllamaRouter | None = None) -> Application:
    # per-chat conversation history and running summary, kept in memory only
    # (reset on restart)
    histories: dict[int, list[dict[str, str]]] = {}
    summaries: dict[int, str] = {}

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
        history.append({"role": "user", "content": text})

        typing_task = asyncio.create_task(_keep_typing(context.bot, chat_id))
        try:
            messages = history[1:]
            over_budget = sum(_estimate_tokens(m["content"]) for m in messages) > config.max_history_tokens
            if over_budget:
                older, recent = _split_recent(messages, config.recent_history_tokens)
                if older:
                    # Compacting means an extra LLM call before the real
                    # reply, so let the user know why this one is slower.
                    await update.message.reply_text(COMPACTING_NOTICE)
                    try:
                        summaries[chat_id] = await _compact_history(llm_client, summaries.get(chat_id, ""), older)
                        history[1:] = recent
                    except Exception:
                        # Compaction failed — fall through to the plain
                        # token-budget trim below as a safety net; older
                        # messages get dropped like before instead of kept.
                        logger.exception("Failed compacting conversation history")

            history[0] = _build_system_message(config, summaries.get(chat_id, ""))
            # bound what we're about to send *before* sending it, not after —
            # trims oldest messages first, whatever number of them that is
            history = _trim_to_token_budget(history, config.max_history_tokens)

            think = await router.classify(text) if router else False
            if think:
                await update.message.reply_text(TOOL_CALL_LABELS["think_harder"]({}))

            tools = resolve_tools(config.enabled_tools)
            try:
                if tools:
                    tool_context = _make_tool_context(context.application, chat_id)
                    reply = await llm_client.chat(
                        history,
                        tools=tools,
                        context=tool_context,
                        on_tool_call=_make_on_tool_call(update),
                        think=think,
                    )
                else:
                    reply = await llm_client.chat(history, think=think)
            except Exception:
                logger.exception("Failed calling the LLM")
                await update.message.reply_text("Something went wrong talking to the model. Please try again.")
                return
        finally:
            typing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await typing_task

        histories[chat_id] = history
        history.append({"role": "assistant", "content": reply})
        await _send_formatted_reply(update, reply)

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
