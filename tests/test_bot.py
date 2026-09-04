import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, MessageHandler

from app.bot import _build_system_message, _is_allowed, _warm_up_ollama, build_application
from app.config import Config


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
    )
    defaults.update(overrides)
    return Config(**defaults)


def make_update(*, user_id=1, text="hello"):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = 42
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def make_context():
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    return context


def get_handlers(app):
    handlers = app.handlers[0]
    start = next(h for h in handlers if isinstance(h, CommandHandler))
    message = next(h for h in handlers if isinstance(h, MessageHandler))
    return start.callback, message.callback


def make_recording_llm_client(replies):
    """An AsyncMock whose .chat records a *snapshot* of the messages it was
    called with, since the real list is mutated further (assistant reply
    appended) right after the call returns."""
    calls: list[list[dict]] = []
    responses = iter(replies)

    def fake_chat(messages):
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
    update.message.reply_text.assert_awaited_once_with("the answer")


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


async def test_handle_message_sends_typing_action_while_waiting():
    config = make_config()
    llm_client = AsyncMock()

    async def slow_chat(messages):
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

    async def slow_failing_chat(messages):
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
    await asyncio.sleep(0)  # let the fire-and-forget warm-up task run

    llm_client.chat.assert_awaited_once_with([{"role": "user", "content": "Hi"}])


async def test_post_init_skips_warmup_for_cloud_backend():
    config = make_config(llm_backend="cloud")
    llm_client = AsyncMock()
    app = build_application(config, llm_client)

    await app.post_init(app)
    await asyncio.sleep(0)

    llm_client.chat.assert_not_called()


async def test_handle_message_trims_history(monkeypatch):
    fixed = datetime(2026, 9, 4, 20, 30)
    freeze_now(monkeypatch, fixed)
    config = make_config()
    llm_client, calls = make_recording_llm_client([f"reply-{i}" for i in range(25)])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    for i in range(25):
        await handle_message(make_update(text=f"msg-{i}"), make_context())

    last_messages = calls[-1]
    assert last_messages[0] == {
        "role": "system",
        "content": expected_system_content("You are Rex.", fixed, "UTC"),
    }
    # MAX_HISTORY_MESSAGES caps the *stored* history at 20; the list passed to
    # chat() can be one longer right before that call's own trim happens.
    assert len(last_messages) <= 21
    assert not any(m.get("content") == "msg-0" for m in last_messages)
