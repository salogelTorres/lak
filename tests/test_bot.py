import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler

import app.bot as bot_module
from app.bot import (
    COMPACTING_NOTICE,
    COMPACTION_SYSTEM_PROMPT,
    EMPTY_REPLY_FALLBACK,
    TOOL_CALL_LABELS,
    VOICE_TRANSCRIPTION_PREFIX,
    _build_system_message,
    _compact_history,
    _estimate_tokens,
    _get_whisper_model,
    _is_allowed,
    _make_on_tool_call,
    _make_tool_context,
    _send_formatted_reply,
    _split_recent,
    _transcribe_sync,
    _trim_to_token_budget,
    _warm_up_ollama,
    build_application,
    transcribe_voice,
)
from app.config import Config


@pytest.fixture(autouse=True)
def clear_whisper_model_cache():
    bot_module._whisper_models.clear()
    yield
    bot_module._whisper_models.clear()


def freeze_now(monkeypatch, fixed: datetime):
    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.replace(tzinfo=tz) if tz else fixed

    monkeypatch.setattr("app.bot.datetime", _FrozenDatetime)


def expected_system_content(system_prompt: str, fixed: datetime, tz_name: str) -> str:
    datetime_line = f"Current date and time: {fixed.strftime('%A, %Y-%m-%d %H:%M')} ({tz_name})"
    return f"{system_prompt}\n\n{datetime_line}"


def make_config(**overrides) -> Config:
    defaults = dict(
        telegram_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        allowed_user_ids=set(),
        agent_name="Rex",
        system_prompt="You are Rex.",
        timezone="UTC",
        llm_backend="ollama",
        ollama_base_url="http://ollama:11434",
        ollama_model="llama3",
        cloud_api_base_url="https://api.example.com/v1",
        cloud_api_key="",
        cloud_model="gpt-4o-mini",
        whisper_model="small",
        max_history_tokens=2000,
        recent_history_tokens=500,
        enabled_tools=[],
        router_model="",
    )
    defaults.update(overrides)
    return Config(**defaults)


def make_update(*, user_id=1, text="hello"):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = 42
    update.message.text = text
    update.message.voice = None
    update.message.audio = None
    update.message.reply_text = AsyncMock()
    return update


def make_voice_update(*, user_id=1, file_id="file123", as_audio=False):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = 42
    update.message.reply_text = AsyncMock()
    voice_obj = MagicMock()
    voice_obj.file_id = file_id
    update.message.voice = None if as_audio else voice_obj
    update.message.audio = voice_obj if as_audio else None
    return update


def make_context():
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    return context


def make_voice_context(audio_bytes=b"fake-audio-bytes"):
    context = make_context()
    telegram_file = MagicMock()
    telegram_file.download_as_bytearray = AsyncMock(return_value=bytearray(audio_bytes))
    context.bot.get_file = AsyncMock(return_value=telegram_file)
    return context


def get_handlers(app):
    handlers = app.handlers[0]
    start = next(h for h in handlers if isinstance(h, CommandHandler))
    message = next(
        h for h in handlers if isinstance(h, MessageHandler) and h.callback.__name__ == "handle_message"
    )
    return start.callback, message.callback


def get_voice_handler(app):
    handlers = app.handlers[0]
    voice = next(
        h for h in handlers if isinstance(h, MessageHandler) and h.callback.__name__ == "handle_voice"
    )
    return voice.callback


def make_recording_llm_client(replies):
    """An AsyncMock whose .chat records a *snapshot* of the messages it was
    called with, since the real list is mutated further (assistant reply
    appended) right after the call returns."""
    calls: list[list[dict]] = []
    responses = iter(replies)

    def fake_chat(messages, **kwargs):
        calls.append([dict(m) for m in messages])
        return next(responses)

    client = AsyncMock()
    client.chat = AsyncMock(side_effect=fake_chat)
    return client, calls


@pytest.mark.parametrize(
    "allowed, user_id, expected",
    [
        (set(), 1, True),
        ({1, 2}, 1, True),
        ({1, 2}, 3, False),
    ],
)
def test_is_allowed(allowed, user_id, expected):
    config = make_config(allowed_user_ids=allowed)
    assert _is_allowed(config, user_id) is expected


def test_build_system_message_includes_current_datetime(monkeypatch):
    fixed = datetime(2026, 9, 4, 20, 30)
    freeze_now(monkeypatch, fixed)
    config = make_config(system_prompt="You are Rex.", timezone="Europe/Madrid")

    message = _build_system_message(config)

    assert message["role"] == "system"
    assert message["content"] == expected_system_content("You are Rex.", fixed, "Europe/Madrid")


def test_build_system_message_falls_back_to_utc_for_unknown_timezone():
    config = make_config(system_prompt="You are Rex.", timezone="Not/AZone")

    message = _build_system_message(config)

    assert "(UTC)" in message["content"]


def test_build_system_message_includes_summary_when_present(monkeypatch):
    config = make_config(system_prompt="You are Rex.", timezone="UTC")

    message = _build_system_message(config, summary="The user's name is Luis.")

    assert "Summary of earlier conversation" in message["content"]
    assert "The user's name is Luis." in message["content"]


def test_build_system_message_omits_summary_section_when_empty():
    config = make_config(system_prompt="You are Rex.", timezone="UTC")

    message = _build_system_message(config, summary="")

    assert "Summary of earlier conversation" not in message["content"]


def test_build_system_message_refreshes_between_calls(monkeypatch):
    config = make_config(system_prompt="You are Rex.", timezone="UTC")

    freeze_now(monkeypatch, datetime(2026, 9, 4, 8, 0))
    first = _build_system_message(config)

    freeze_now(monkeypatch, datetime(2026, 9, 4, 20, 0))
    second = _build_system_message(config)

    assert first["content"] != second["content"]
    assert "08:00" in first["content"]
    assert "20:00" in second["content"]


async def test_start_replies_with_greeting():
    config = make_config()
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    start, _ = get_handlers(app)

    update = make_update()
    await start(update, make_context())

    update.message.reply_text.assert_awaited_once_with("Hi, I'm Rex. How can I help?")


async def test_handle_message_replies_with_llm_output(monkeypatch):
    fixed = datetime(2026, 9, 4, 20, 30)
    freeze_now(monkeypatch, fixed)
    config = make_config()
    llm_client, calls = make_recording_llm_client(["the answer"])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update(text="what's up?")
    await handle_message(update, make_context())

    llm_client.chat.assert_awaited_once()
    sent_messages = calls[0]
    assert sent_messages[0] == {
        "role": "system",
        "content": expected_system_content("You are Rex.", fixed, "UTC"),
    }
    assert sent_messages[-1] == {"role": "user", "content": "what's up?"}
    update.message.reply_text.assert_awaited_once_with("the answer", parse_mode=ParseMode.MARKDOWN)


async def test_handle_message_keeps_history_across_calls():
    config = make_config()
    llm_client, calls = make_recording_llm_client(["first", "second"])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(text="one"), make_context())
    await handle_message(make_update(text="two"), make_context())

    second_call_messages = calls[1]
    roles_and_content = [(m["role"], m["content"]) for m in second_call_messages]
    assert ("user", "one") in roles_and_content
    assert ("assistant", "first") in roles_and_content
    assert ("user", "two") in roles_and_content


async def test_handle_message_refreshes_datetime_across_calls(monkeypatch):
    config = make_config()
    llm_client, calls = make_recording_llm_client(["first", "second"])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    freeze_now(monkeypatch, datetime(2026, 9, 4, 8, 0))
    await handle_message(make_update(text="one"), make_context())

    freeze_now(monkeypatch, datetime(2026, 9, 4, 20, 0))
    await handle_message(make_update(text="two"), make_context())

    first_system_content = calls[0][0]["content"]
    second_system_content = calls[1][0]["content"]
    assert first_system_content != second_system_content
    assert "08:00" in first_system_content
    assert "20:00" in second_system_content


async def test_handle_message_passes_enabled_tools_to_the_llm():
    from app.tools.web_search import TOOL as SEARCH_WEB_TOOL

    config = make_config(enabled_tools=["search_web"])
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(text="search something"), make_context())

    llm_client.chat.assert_awaited_once()
    kwargs = llm_client.chat.call_args.kwargs
    assert kwargs["tools"] == [SEARCH_WEB_TOOL]
    assert kwargs["context"].chat_id == 42
    assert callable(kwargs["on_tool_call"])


async def test_handle_message_omits_tools_kwarg_when_none_enabled():
    config = make_config(enabled_tools=[])
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(), make_context())

    assert llm_client.chat.call_args.kwargs == {"think": False}


async def test_handle_message_ignores_unknown_tool_names():
    config = make_config(enabled_tools=["not_a_real_tool"])
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(), make_context())

    assert llm_client.chat.call_args.kwargs == {"think": False}


async def test_handle_message_without_router_never_calls_classify():
    config = make_config()
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    app = build_application(config, llm_client, router=None)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(), make_context())

    assert llm_client.chat.call_args.kwargs == {"think": False}


async def test_handle_message_with_router_says_think_passes_think_true_and_notifies():
    config = make_config()
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    router = AsyncMock()
    router.classify.return_value = True
    app = build_application(config, llm_client, router=router)
    _, handle_message = get_handlers(app)
    update = make_update(text="a tricky riddle")

    await handle_message(update, make_context())

    router.classify.assert_awaited_once_with("a tricky riddle")
    assert llm_client.chat.call_args.kwargs == {"think": True}
    update.message.reply_text.assert_any_call(TOOL_CALL_LABELS["think_harder"]({}))


async def test_handle_message_with_router_says_no_think_sends_no_notice():
    config = make_config()
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    router = AsyncMock()
    router.classify.return_value = False
    app = build_application(config, llm_client, router=router)
    _, handle_message = get_handlers(app)
    update = make_update(text="hola")

    await handle_message(update, make_context())

    assert llm_client.chat.call_args.kwargs == {"think": False}
    assert TOOL_CALL_LABELS["think_harder"]({}) not in [
        call.args[0] for call in update.message.reply_text.await_args_list
    ]


async def test_handle_message_with_router_and_tools_passes_think_through():
    from app.tools.web_search import TOOL as SEARCH_WEB_TOOL

    config = make_config(enabled_tools=["search_web"])
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    router = AsyncMock()
    router.classify.return_value = True
    app = build_application(config, llm_client, router=router)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(text="a tricky riddle"), make_context())

    kwargs = llm_client.chat.call_args.kwargs
    assert kwargs["think"] is True
    assert kwargs["tools"] == [SEARCH_WEB_TOOL]


async def test_handle_message_with_router_think_excludes_think_harder_tool():
    # The router already turns on extended reasoning for this turn — the
    # model must not also be offered think_harder, or it can redundantly
    # self-invoke it on top of that (a second full reasoning round,
    # announced with the exact same notice text sent for the router).
    from app.tools.web_search import TOOL as SEARCH_WEB_TOOL

    config = make_config(enabled_tools=["search_web", "think_harder"])
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    router = AsyncMock()
    router.classify.return_value = True
    app = build_application(config, llm_client, router=router)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(text="a tricky riddle"), make_context())

    assert llm_client.chat.call_args.kwargs["tools"] == [SEARCH_WEB_TOOL]


async def test_handle_message_without_think_still_offers_think_harder_tool():
    from app.tools.think_harder import TOOL as THINK_HARDER_TOOL

    config = make_config(enabled_tools=["think_harder"])
    llm_client = AsyncMock()
    llm_client.chat.return_value = "the answer"
    router = AsyncMock()
    router.classify.return_value = False
    app = build_application(config, llm_client, router=router)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(text="hola"), make_context())

    assert llm_client.chat.call_args.kwargs["tools"] == [THINK_HARDER_TOOL]


async def test_handle_message_relays_tool_call_notifications_to_telegram():
    config = make_config(enabled_tools=["search_web"])
    llm_client = AsyncMock()

    async def fake_chat(messages, tools=None, context=None, on_tool_call=None, think=False):
        if on_tool_call:
            await on_tool_call("search_web", {"query": "Billy the bot"})
        return "the answer"

    llm_client.chat = AsyncMock(side_effect=fake_chat)
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)
    update = make_update(text="search something")

    await handle_message(update, make_context())

    update.message.reply_text.assert_any_call(TOOL_CALL_LABELS["search_web"]({"query": "Billy the bot"}))
    update.message.reply_text.assert_any_call("the answer", parse_mode=ParseMode.MARKDOWN)


def make_fake_application():
    # A real ptb Application's `.bot` is a frozen TelegramObject that
    # refuses attribute overrides, so send_message can't be mocked on it
    # directly — a lightweight stand-in exercises the same two attributes
    # _make_tool_context actually uses (bot_data, bot.send_message).
    application = MagicMock()
    application.bot_data = {}
    application.bot.send_message = AsyncMock()
    return application


async def test_make_tool_context_returns_context_with_given_chat_id():
    app = make_fake_application()

    context = _make_tool_context(app, 42)

    assert context.chat_id == 42


async def test_schedule_reminder_sends_message_after_delay():
    app = make_fake_application()
    context = _make_tool_context(app, 42)

    # A real (if tiny) delay rather than a mocked-instant asyncio.sleep:
    # with cleanup now happening via add_done_callback (see the race that
    # motivated it, below), a zero-time sleep could let _fire() finish and
    # remove itself before this test even gets to look at reminder_tasks.
    # Mirrors the real call path too: every tool, needs_context or not,
    # runs via asyncio.to_thread (see app.llm._call_tool) — a worker thread
    # with no event loop of its own. Calling schedule_reminder() straight
    # from this coroutine would miss the bug this covers (asyncio.create_task
    # requires a loop running in the *current* thread).
    await asyncio.to_thread(context.schedule_reminder, 0.05, "Call mom")
    task = next(iter(app.bot_data["reminder_tasks"]))
    await asyncio.wrap_future(task)

    app.bot.send_message.assert_awaited_once_with(42, "⏰ Reminder: Call mom")


async def test_schedule_reminder_task_removes_itself_once_done():
    # Regression test for the same asyncio gotcha as the warm-up task: the
    # task must be stored somewhere (bot_data) while pending, and cleaned up
    # afterward instead of leaking forever in that set.
    app = make_fake_application()
    context = _make_tool_context(app, 42)

    await asyncio.to_thread(context.schedule_reminder, 0.05, "Call mom")
    task = next(iter(app.bot_data["reminder_tasks"]))
    await asyncio.wrap_future(task)

    assert app.bot_data["reminder_tasks"] == set()


async def test_schedule_reminder_logs_instead_of_raising_on_send_failure(caplog):
    app = make_fake_application()
    app.bot.send_message = AsyncMock(side_effect=RuntimeError("network down"))
    context = _make_tool_context(app, 42)

    await asyncio.to_thread(context.schedule_reminder, 0.05, "Call mom")
    task = next(iter(app.bot_data["reminder_tasks"]))

    with caplog.at_level(logging.ERROR, logger="app.bot"):
        await asyncio.wrap_future(task)  # must not raise

    assert "failed sending reminder" in caplog.text.lower()


async def test_on_tool_call_includes_the_argument_in_the_label():
    update = make_update()
    on_tool_call = _make_on_tool_call(update)

    await on_tool_call("search_web", {"query": "billy bot"})

    update.message.reply_text.assert_awaited_once_with("🔍 Searching the web for: billy bot")


async def test_on_tool_call_falls_back_to_plain_label_when_argument_is_missing():
    update = make_update()
    on_tool_call = _make_on_tool_call(update)

    await on_tool_call("search_web", {})

    update.message.reply_text.assert_awaited_once_with("🔍 Searching the web...")


async def test_on_tool_call_truncates_a_long_argument():
    update = make_update()
    on_tool_call = _make_on_tool_call(update)

    await on_tool_call("fetch_page", {"url": "https://example.com/" + "x" * 300})

    sent = update.message.reply_text.await_args.args[0]
    assert len(sent) < 300
    assert sent.endswith("…")


async def test_on_tool_call_falls_back_to_generic_label_for_unknown_tool():
    update = make_update()
    on_tool_call = _make_on_tool_call(update)

    await on_tool_call("some_future_tool", {})

    update.message.reply_text.assert_awaited_once_with("🔧 Using some_future_tool...")


async def test_on_tool_call_recovers_from_a_formatter_that_raises():
    update = make_update()
    on_tool_call = _make_on_tool_call(update)

    # remind_me's formatter does `args["minutes"]:g`, which raises for a
    # non-numeric value — a model sending an odd type must not take the
    # whole reply down with it.
    await on_tool_call("remind_me", {"minutes": "soon", "message": "hi"})

    update.message.reply_text.assert_awaited_once_with("🔧 Using remind_me...")


async def test_send_formatted_reply_uses_markdown_parse_mode():
    update = make_update()

    await _send_formatted_reply(update, "**bold**")

    update.message.reply_text.assert_awaited_once_with("**bold**", parse_mode=ParseMode.MARKDOWN)


async def test_send_formatted_reply_falls_back_to_plain_text_on_bad_markdown(caplog):
    update = make_update()
    update.message.reply_text = AsyncMock(side_effect=[BadRequest("Can't parse entities"), None])

    with caplog.at_level(logging.WARNING, logger="app.bot"):
        await _send_formatted_reply(update, "unbalanced *bold")

    assert update.message.reply_text.await_args_list[0].args == ("unbalanced *bold",)
    assert update.message.reply_text.await_args_list[0].kwargs == {"parse_mode": ParseMode.MARKDOWN}
    assert update.message.reply_text.await_args_list[1].args == ("unbalanced *bold",)
    assert "wasn't valid markdown" in caplog.text.lower()


async def test_handle_message_denies_disallowed_user():
    config = make_config(allowed_user_ids={99})
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update(user_id=1)
    await handle_message(update, make_context())

    llm_client.chat.assert_not_called()
    update.message.reply_text.assert_awaited_once_with("You don't have access to this bot.")


async def test_handle_message_denies_when_user_is_none():
    config = make_config()
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update()
    update.effective_user = None
    await handle_message(update, make_context())

    llm_client.chat.assert_not_called()
    update.message.reply_text.assert_awaited_once_with("You don't have access to this bot.")


async def test_handle_message_reports_llm_error():
    config = make_config()
    llm_client = AsyncMock()
    llm_client.chat.side_effect = RuntimeError("boom")
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update()
    await handle_message(update, make_context())

    update.message.reply_text.assert_awaited_once_with(
        "Something went wrong talking to the model. Please try again."
    )


async def test_handle_message_falls_back_when_llm_returns_an_empty_reply(caplog):
    # Telegram's sendMessage rejects an empty string outright, and it's the
    # same empty text either way, so the no-parse-mode retry in
    # _send_formatted_reply can't save it — seen in practice when a model
    # burns every tool round still trying to call more tools and answers
    # with nothing in the final, tools-withheld round.
    config = make_config()
    llm_client = AsyncMock()
    llm_client.chat.return_value = ""
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update()
    with caplog.at_level(logging.WARNING, logger="app.bot"):
        await handle_message(update, make_context())

    update.message.reply_text.assert_awaited_once_with(EMPTY_REPLY_FALLBACK, parse_mode=ParseMode.MARKDOWN)
    assert "empty reply" in caplog.text.lower()


async def test_handle_message_sends_typing_action_while_waiting():
    config = make_config()
    llm_client = AsyncMock()

    async def slow_chat(messages, **kwargs):
        # a real await point, so the concurrently-scheduled typing task gets
        # a chance to run before this resolves — unlike a mock that returns
        # without ever suspending (which is what a real, slow LLM call never
        # does in practice).
        await asyncio.sleep(0)
        return "the answer"

    llm_client.chat = AsyncMock(side_effect=slow_chat)
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    context = make_context()
    await handle_message(make_update(), context)

    context.bot.send_chat_action.assert_awaited_with(chat_id=42, action=ChatAction.TYPING)


async def test_handle_message_stops_typing_action_on_llm_error():
    config = make_config()
    llm_client = AsyncMock()

    async def slow_failing_chat(messages, **kwargs):
        await asyncio.sleep(0)
        raise RuntimeError("boom")

    llm_client.chat = AsyncMock(side_effect=slow_failing_chat)
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    context = make_context()
    await handle_message(make_update(), context)

    context.bot.send_chat_action.assert_awaited_with(chat_id=42, action=ChatAction.TYPING)


async def test_warm_up_ollama_sends_a_throwaway_message_and_logs(caplog):
    llm_client = AsyncMock()
    llm_client.chat.return_value = "hi there"

    with caplog.at_level(logging.INFO, logger="app.bot"):
        await _warm_up_ollama(llm_client)

    llm_client.chat.assert_awaited_once_with([{"role": "user", "content": "Hi"}])
    assert "warmed up" in caplog.text.lower()


async def test_warm_up_ollama_retries_while_ollama_is_still_starting(monkeypatch, caplog):
    llm_client = AsyncMock()
    llm_client.chat.side_effect = [ConnectionError("not up yet"), ConnectionError("not up yet"), "hi there"]
    sleep_mock = AsyncMock()
    monkeypatch.setattr("app.bot.asyncio.sleep", sleep_mock)

    with caplog.at_level(logging.INFO, logger="app.bot"):
        await _warm_up_ollama(llm_client, retries=5, delay_seconds=0)

    assert llm_client.chat.await_count == 3
    assert sleep_mock.await_count == 2
    assert "warmed up" in caplog.text.lower()


async def test_warm_up_ollama_logs_warning_after_exhausting_retries(monkeypatch, caplog):
    llm_client = AsyncMock()
    llm_client.chat.side_effect = RuntimeError("boom")
    monkeypatch.setattr("app.bot.asyncio.sleep", AsyncMock())

    with caplog.at_level(logging.WARNING, logger="app.bot"):
        await _warm_up_ollama(llm_client, retries=3, delay_seconds=0)  # must not raise

    assert llm_client.chat.await_count == 3
    assert "warm-up failed" in caplog.text.lower()


async def test_warm_up_ollama_noop_with_zero_retries():
    llm_client = AsyncMock()

    await _warm_up_ollama(llm_client, retries=0)

    llm_client.chat.assert_not_called()


async def test_post_init_warms_up_ollama_backend():
    config = make_config(llm_backend="ollama")
    llm_client = AsyncMock()
    app = build_application(config, llm_client)

    await app.post_init(app)
    await app.bot_data["warm_up_task"]

    llm_client.chat.assert_awaited_once_with([{"role": "user", "content": "Hi"}])


async def test_post_init_skips_warmup_for_cloud_backend():
    config = make_config(llm_backend="cloud")
    llm_client = AsyncMock()
    app = build_application(config, llm_client)

    await app.post_init(app)
    await asyncio.sleep(0)

    llm_client.chat.assert_not_called()
    assert "warm_up_task" not in app.bot_data


async def test_post_init_keeps_a_strong_reference_to_the_warm_up_task():
    # Regression test: asyncio only keeps a *weak* reference to a task, so a
    # fire-and-forget task with no reference stored anywhere can be
    # garbage-collected before it finishes (see asyncio.create_task docs).
    # It must be stashed somewhere (bot_data) that outlives post_init().
    config = make_config(llm_backend="ollama")
    llm_client = AsyncMock()
    app = build_application(config, llm_client)

    await app.post_init(app)

    task = app.bot_data["warm_up_task"]
    assert isinstance(task, asyncio.Task)
    assert not task.done()  # still referenced, not already GC'd/cancelled
    await task


def _msg(role: str, content: str) -> dict[str, str]:
    return {"role": role, "content": content}


def test_estimate_tokens_uses_chars_per_token_heuristic():
    assert _estimate_tokens("") == 1  # never zero — an empty message still costs something
    assert _estimate_tokens("abcd") == 1
    assert _estimate_tokens("a" * 40) == 10


def test_trim_to_token_budget_keeps_everything_when_it_fits():
    history = [_msg("system", "sys"), _msg("user", "hi"), _msg("assistant", "hello")]

    assert _trim_to_token_budget(history, max_tokens=1000) == history


def test_trim_to_token_budget_always_keeps_system_and_newest_even_if_over_budget():
    history = [_msg("system", "s" * 4), _msg("user", "a" * 4000)]

    result = _trim_to_token_budget(history, max_tokens=10)

    assert result == history


def test_trim_to_token_budget_drops_oldest_first_regardless_of_message_count():
    history = [
        _msg("system", "s"),
        _msg("user", "a" * 4000),  # huge, oldest non-system message
        _msg("assistant", "b" * 8),
        _msg("user", "c" * 8),  # newest
    ]

    result = _trim_to_token_budget(history, max_tokens=10)

    contents = [m["content"] for m in result]
    assert "a" * 4000 not in contents  # the one huge message got dropped...
    assert "b" * 8 in contents  # ...even though these two small ones fit
    assert result[0]["role"] == "system"
    assert result[-1]["content"] == "c" * 8


def test_trim_to_token_budget_with_only_a_system_message():
    history = [_msg("system", "sys")]

    assert _trim_to_token_budget(history, max_tokens=1000) == history


def test_split_recent_keeps_everything_as_recent_when_it_fits():
    messages = [_msg("user", "a" * 8), _msg("assistant", "b" * 8)]

    older, recent = _split_recent(messages, recent_tokens=1000)

    assert older == []
    assert recent == messages


def test_split_recent_with_no_messages():
    assert _split_recent([], recent_tokens=1000) == ([], [])


def test_split_recent_always_keeps_at_least_the_newest_message():
    messages = [_msg("user", "a" * 40), _msg("assistant", "b" * 4000)]

    older, recent = _split_recent(messages, recent_tokens=1)

    assert recent == [messages[-1]]
    assert older == messages[:-1]


def test_split_recent_puts_oldest_messages_into_older_regardless_of_count():
    messages = [
        _msg("user", "a" * 4000),  # huge, oldest
        _msg("assistant", "b" * 8),
        _msg("user", "c" * 8),  # newest
    ]

    older, recent = _split_recent(messages, recent_tokens=10)

    assert older == [messages[0]]
    assert recent == messages[1:]


async def test_compact_history_summarizes_messages_without_existing_summary():
    llm_client = AsyncMock()
    llm_client.chat.return_value = "  A concise summary.  "
    messages = [_msg("user", "hi"), _msg("assistant", "hello there")]

    summary = await _compact_history(llm_client, "", messages)

    assert summary == "A concise summary."
    sent = llm_client.chat.call_args.args[0]
    assert sent[0] == {"role": "system", "content": COMPACTION_SYSTEM_PROMPT}
    assert "Existing summary" not in sent[1]["content"]
    assert "user: hi" in sent[1]["content"]
    assert "assistant: hello there" in sent[1]["content"]


async def test_compact_history_folds_in_existing_summary():
    llm_client = AsyncMock()
    llm_client.chat.return_value = "Updated summary."
    messages = [_msg("user", "what's my name?")]

    await _compact_history(llm_client, "The user's name is Luis.", messages)

    sent = llm_client.chat.call_args.args[0]
    assert "Existing summary:\nThe user's name is Luis." in sent[1]["content"]
    assert "New messages to fold in:" in sent[1]["content"]


async def test_handle_message_compacts_older_history_once_over_budget(monkeypatch):
    fixed = datetime(2026, 9, 4, 20, 30)
    freeze_now(monkeypatch, fixed)
    # Small enough that a handful of messages push it over budget, with a
    # recent window tight enough that some of them fall outside it.
    config = make_config(max_history_tokens=15, recent_history_tokens=5)

    def fake_chat(messages, **kwargs):
        if messages[0]["content"] == COMPACTION_SYSTEM_PROMPT:
            return "Summary: talked about the weather."
        return "reply"

    llm_client = AsyncMock()
    llm_client.chat = AsyncMock(side_effect=fake_chat)
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    updates = []
    for i in range(5):
        update = make_update(text=f"message number {i}" * 3)
        updates.append(update)
        await handle_message(update, make_context())

    # The compaction notice went out on at least one of these turns.
    notices = [
        call.args[0]
        for update in updates
        for call in update.message.reply_text.await_args_list
        if call.args and call.args[0] == COMPACTING_NOTICE
    ]
    assert notices

    # The next turn's system message carries the summary forward.
    another_update = make_update(text="one more")
    await handle_message(another_update, make_context())
    system_content = llm_client.chat.call_args_list[-1].args[0][0]["content"]
    assert "talked about the weather" in system_content


async def test_handle_message_falls_back_to_trimming_when_compaction_fails(monkeypatch, caplog):
    fixed = datetime(2026, 9, 4, 20, 30)
    freeze_now(monkeypatch, fixed)
    config = make_config(max_history_tokens=15, recent_history_tokens=5)

    def fake_chat(messages, **kwargs):
        if messages[0]["content"] == COMPACTION_SYSTEM_PROMPT:
            raise RuntimeError("boom")
        return "reply"

    llm_client = AsyncMock()
    llm_client.chat = AsyncMock(side_effect=fake_chat)
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    with caplog.at_level(logging.ERROR, logger="app.bot"):
        for i in range(5):
            update = make_update(text=f"message number {i}" * 3)
            await handle_message(update, make_context())

    assert "compacting" in caplog.text.lower()
    # The bot still replied normally despite the compaction failure.
    update.message.reply_text.assert_awaited_with("reply", parse_mode=ParseMode.MARKDOWN)


async def test_handle_message_does_not_compact_when_recent_window_covers_everything():
    config = make_config(max_history_tokens=10, recent_history_tokens=10_000)
    llm_client, calls = make_recording_llm_client([f"reply-{i}" for i in range(5)])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    updates = []
    for i in range(5):
        update = make_update(text=f"message number {i}")
        updates.append(update)
        await handle_message(update, make_context())

    assert all(
        call.args[0] != COMPACTING_NOTICE
        for update in updates
        for call in update.message.reply_text.await_args_list
    )
    assert all(m["role"] != "system" or COMPACTION_SYSTEM_PROMPT not in m["content"] for m in calls[-1])


async def test_handle_message_over_budget_with_nothing_old_enough_to_compact():
    # over budget, but the recent window alone already covers every message
    # (older is empty) — must fall straight through to the plain trim
    # without ever attempting compaction.
    config = make_config(max_history_tokens=0, recent_history_tokens=10_000)
    llm_client, calls = make_recording_llm_client(["ok"])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update(text="hi")
    await handle_message(update, make_context())

    assert all(call.args[0] != COMPACTING_NOTICE for call in update.message.reply_text.await_args_list)
    update.message.reply_text.assert_awaited_with("ok", parse_mode=ParseMode.MARKDOWN)


async def test_handle_message_trims_by_token_budget_not_message_count(monkeypatch):
    fixed = datetime(2026, 9, 4, 20, 30)
    freeze_now(monkeypatch, fixed)
    # A tiny budget forces trimming after just a couple of short messages —
    # proving it's governed by tokens, not a fixed message-count cap.
    config = make_config(max_history_tokens=30)
    llm_client, calls = make_recording_llm_client([f"reply-{i}" for i in range(5)])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    for i in range(5):
        await handle_message(make_update(text=f"message number {i}"), make_context())

    last_messages = calls[-1]
    assert last_messages[0]["role"] == "system"
    assert last_messages[-1]["content"] == "message number 4"
    assert not any(m["content"] == "message number 0" for m in last_messages)


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeWhisperModel:
    """Records how it was constructed and returns canned segments."""

    instances: list["FakeWhisperModel"] = []

    def __init__(self, model_name, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs
        self.transcribed_with: list = []
        FakeWhisperModel.instances.append(self)

    def transcribe(self, audio_file):
        self.transcribed_with.append(audio_file)
        return [FakeSegment(" hello "), FakeSegment("world ")], object()


def test_get_whisper_model_uses_expected_params(monkeypatch):
    monkeypatch.setattr(bot_module, "WhisperModel", FakeWhisperModel)
    FakeWhisperModel.instances = []

    model = _get_whisper_model("small")

    assert isinstance(model, FakeWhisperModel)
    assert model.model_name == "small"
    assert model.kwargs == {"device": "cpu", "compute_type": "int8", "download_root": bot_module.WHISPER_DOWNLOAD_ROOT}


def test_get_whisper_model_caches_instance_per_model_name(monkeypatch):
    monkeypatch.setattr(bot_module, "WhisperModel", FakeWhisperModel)
    FakeWhisperModel.instances = []

    first = _get_whisper_model("small")
    second = _get_whisper_model("small")
    third = _get_whisper_model("medium")

    assert first is second
    assert third is not first
    assert len(FakeWhisperModel.instances) == 2


def test_transcribe_sync_joins_segment_text(monkeypatch):
    monkeypatch.setattr(bot_module, "WhisperModel", FakeWhisperModel)

    result = _transcribe_sync(b"raw-audio-bytes", "small")

    assert result == "hello world"


async def test_transcribe_voice_delegates_to_sync_function(monkeypatch):
    monkeypatch.setattr(
        bot_module, "_transcribe_sync", lambda audio, model_name: f"{model_name}:{len(audio)}"
    )

    result = await transcribe_voice(b"1234", "small")

    assert result == "small:4"


async def test_handle_voice_transcribes_and_replies(monkeypatch):
    config = make_config()
    llm_client, calls = make_recording_llm_client(["got it"])
    app = build_application(config, llm_client)
    handle_voice = get_voice_handler(app)

    monkeypatch.setattr(bot_module, "transcribe_voice", AsyncMock(return_value="hola que tal"))

    update = make_voice_update()
    context = make_voice_context()
    await handle_voice(update, context)

    context.bot.get_file.assert_awaited_once_with("file123")
    sent_messages = calls[0]
    assert sent_messages[-1] == {
        "role": "user",
        "content": f"{VOICE_TRANSCRIPTION_PREFIX}: hola que tal",
    }
    update.message.reply_text.assert_awaited_once_with("got it", parse_mode=ParseMode.MARKDOWN)


async def test_handle_voice_accepts_audio_files_too(monkeypatch):
    config = make_config()
    llm_client, calls = make_recording_llm_client(["got it"])
    app = build_application(config, llm_client)
    handle_voice = get_voice_handler(app)

    monkeypatch.setattr(bot_module, "transcribe_voice", AsyncMock(return_value="hola"))

    update = make_voice_update(as_audio=True)
    context = make_voice_context()
    await handle_voice(update, context)

    context.bot.get_file.assert_awaited_once_with("file123")
    assert calls[0][-1]["content"] == f"{VOICE_TRANSCRIPTION_PREFIX}: hola"


async def test_handle_voice_denies_disallowed_user():
    config = make_config(allowed_user_ids={99})
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    handle_voice = get_voice_handler(app)

    update = make_voice_update(user_id=1)
    context = make_voice_context()
    await handle_voice(update, context)

    context.bot.get_file.assert_not_called()
    update.message.reply_text.assert_awaited_once_with("You don't have access to this bot.")


async def test_handle_voice_reports_transcription_failure(monkeypatch):
    config = make_config()
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    handle_voice = get_voice_handler(app)

    monkeypatch.setattr(bot_module, "transcribe_voice", AsyncMock(side_effect=RuntimeError("boom")))

    update = make_voice_update()
    context = make_voice_context()
    await handle_voice(update, context)

    llm_client.chat.assert_not_called()
    update.message.reply_text.assert_awaited_once_with(
        "Couldn't transcribe that voice message. Please try again or send it as text."
    )


async def test_handle_voice_reports_empty_transcription(monkeypatch):
    config = make_config()
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    handle_voice = get_voice_handler(app)

    monkeypatch.setattr(bot_module, "transcribe_voice", AsyncMock(return_value="   "))

    update = make_voice_update()
    context = make_voice_context()
    await handle_voice(update, context)

    llm_client.chat.assert_not_called()
    update.message.reply_text.assert_awaited_once_with(
        "I couldn't make out any speech in that voice message."
    )
