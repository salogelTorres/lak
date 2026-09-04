from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.ext import CommandHandler, MessageHandler

from app.bot import _is_allowed, build_application
from app.config import Config


def make_config(**overrides) -> Config:
    defaults = dict(
        telegram_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        allowed_user_ids=set(),
        agent_name="Rex",
        system_prompt="You are Rex.",
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


async def test_start_replies_with_greeting():
    config = make_config()
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    start, _ = get_handlers(app)

    update = make_update()
    await start(update, MagicMock())

    update.message.reply_text.assert_awaited_once_with("Hi, I'm Rex. How can I help?")


async def test_handle_message_replies_with_llm_output():
    config = make_config()
    llm_client, calls = make_recording_llm_client(["the answer"])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update(text="what's up?")
    await handle_message(update, MagicMock())

    llm_client.chat.assert_awaited_once()
    sent_messages = calls[0]
    assert sent_messages[0] == {"role": "system", "content": "You are Rex."}
    assert sent_messages[-1] == {"role": "user", "content": "what's up?"}
    update.message.reply_text.assert_awaited_once_with("the answer")


async def test_handle_message_keeps_history_across_calls():
    config = make_config()
    llm_client, calls = make_recording_llm_client(["first", "second"])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    await handle_message(make_update(text="one"), MagicMock())
    await handle_message(make_update(text="two"), MagicMock())

    second_call_messages = calls[1]
    roles_and_content = [(m["role"], m["content"]) for m in second_call_messages]
    assert ("user", "one") in roles_and_content
    assert ("assistant", "first") in roles_and_content
    assert ("user", "two") in roles_and_content


async def test_handle_message_denies_disallowed_user():
    config = make_config(allowed_user_ids={99})
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update(user_id=1)
    await handle_message(update, MagicMock())

    llm_client.chat.assert_not_called()
    update.message.reply_text.assert_awaited_once_with("You don't have access to this bot.")


async def test_handle_message_denies_when_user_is_none():
    config = make_config()
    llm_client = AsyncMock()
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update()
    update.effective_user = None
    await handle_message(update, MagicMock())

    llm_client.chat.assert_not_called()
    update.message.reply_text.assert_awaited_once_with("You don't have access to this bot.")


async def test_handle_message_reports_llm_error():
    config = make_config()
    llm_client = AsyncMock()
    llm_client.chat.side_effect = RuntimeError("boom")
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    update = make_update()
    await handle_message(update, MagicMock())

    update.message.reply_text.assert_awaited_once_with(
        "Something went wrong talking to the model. Please try again."
    )


async def test_handle_message_trims_history():
    config = make_config()
    llm_client, calls = make_recording_llm_client([f"reply-{i}" for i in range(25)])
    app = build_application(config, llm_client)
    _, handle_message = get_handlers(app)

    for i in range(25):
        await handle_message(make_update(text=f"msg-{i}"), MagicMock())

    last_messages = calls[-1]
    assert last_messages[0] == {"role": "system", "content": "You are Rex."}
    # MAX_HISTORY_MESSAGES caps the *stored* history at 20; the list passed to
    # chat() can be one longer right before that call's own trim happens.
    assert len(last_messages) <= 21
    assert not any(m.get("content") == "msg-0" for m in last_messages)
