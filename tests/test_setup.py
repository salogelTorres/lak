from unittest.mock import MagicMock

import pytest

import setup


@pytest.fixture
def env_paths(tmp_path, monkeypatch):
    env_example = tmp_path / ".env.example"
    env_example.write_text(
        "# a comment\n\nTELEGRAM_BOT_TOKEN=\nAGENT_NAME=Assistant\n",
        encoding="utf-8",
    )
    env_file = tmp_path / ".env"

    prompt_dir = tmp_path / "app" / "prompts"
    prompt_dir.mkdir(parents=True)
    prompt_example = prompt_dir / "system_prompt.txt.example"
    prompt_example.write_text("You are {{AGENT_NAME}}.", encoding="utf-8")
    prompt_file = prompt_dir / "system_prompt.txt"

    monkeypatch.setattr(setup, "ENV_EXAMPLE", env_example)
    monkeypatch.setattr(setup, "ENV_FILE", env_file)
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "SYSTEM_PROMPT_EXAMPLE", prompt_example)
    monkeypatch.setattr(setup, "SYSTEM_PROMPT_FILE", prompt_file)
    return env_example, env_file


def test_parse_env_example_skips_comments_and_blanks(env_paths):
    entries = setup.parse_env_example()
    assert entries == [("TELEGRAM_BOT_TOKEN", ""), ("AGENT_NAME", "Assistant")]


def test_ask_uses_input_value(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "custom")
    assert setup.ask("AGENT_NAME", "Assistant") == "custom"


def test_ask_falls_back_to_default_on_empty_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "  ")
    assert setup.ask("AGENT_NAME", "Assistant") == "Assistant"


def test_ask_uses_key_as_label_for_unknown_key(monkeypatch):
    seen_prompt = {}

    def fake_input(prompt):
        seen_prompt["value"] = prompt
        return "x"

    monkeypatch.setattr("builtins.input", fake_input)
    setup.ask("SOME_UNKNOWN_KEY", "")
    assert seen_prompt["value"] == "SOME_UNKNOWN_KEY: "


def test_ensure_system_prompt_copies_from_example(env_paths):
    setup.ensure_system_prompt()
    assert setup.SYSTEM_PROMPT_FILE.read_text(encoding="utf-8") == "You are {{AGENT_NAME}}."


def test_ensure_system_prompt_does_not_overwrite_existing_file(env_paths):
    setup.SYSTEM_PROMPT_FILE.write_text("custom personality", encoding="utf-8")
    setup.ensure_system_prompt()
    assert setup.SYSTEM_PROMPT_FILE.read_text(encoding="utf-8") == "custom personality"


def test_ensure_system_prompt_noop_without_example(env_paths):
    setup.SYSTEM_PROMPT_EXAMPLE.unlink()
    setup.ensure_system_prompt()
    assert not setup.SYSTEM_PROMPT_FILE.exists()


def test_main_creates_system_prompt_on_first_run(env_paths, monkeypatch):
    responses = iter(["my-token", "Rex"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)

    setup.main()

    assert setup.SYSTEM_PROMPT_FILE.exists()


def test_main_declines_overwrite(env_paths, monkeypatch, capsys):
    _, env_file = env_paths
    env_file.write_text("EXISTING=1\n", encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    setup.main()

    assert env_file.read_text(encoding="utf-8") == "EXISTING=1\n"
    assert "Cancelled" in capsys.readouterr().out


def test_main_accepts_overwrite_and_proceeds(env_paths, monkeypatch, capsys):
    _, env_file = env_paths
    env_file.write_text("EXISTING=1\n", encoding="utf-8")

    responses = iter(["y", "my-token", "Rex"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)

    setup.main()

    content = env_file.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=my-token" in content
    assert "== Agent configuration ==" in capsys.readouterr().out


def test_main_writes_env_and_skips_launch_without_docker(env_paths, monkeypatch, capsys):
    _, env_file = env_paths
    responses = iter(["my-token", "Rex"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    run_mock = MagicMock()
    monkeypatch.setattr(setup.subprocess, "run", run_mock)

    setup.main()

    content = env_file.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=my-token" in content
    assert "AGENT_NAME=Rex" in content
    run_mock.assert_not_called()
    assert "Docker was not found" in capsys.readouterr().out


def test_main_creates_env_when_missing_without_prompting_overwrite(env_paths, monkeypatch):
    responses = iter(["my-token", "Rex", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/bin/docker")
    run_mock = MagicMock()
    monkeypatch.setattr(setup.subprocess, "run", run_mock)

    setup.main()

    run_mock.assert_not_called()


def test_main_launches_docker_compose_when_confirmed(env_paths, monkeypatch, capsys):
    responses = iter(["my-token", "Rex", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/bin/docker")
    run_mock = MagicMock()
    monkeypatch.setattr(setup.subprocess, "run", run_mock)

    setup.main()

    run_mock.assert_called_once_with(
        ["docker", "compose", "up", "-d", "--build"], cwd=setup.ROOT, check=False
    )
    assert "Agent is up" in capsys.readouterr().out


def test_cli_returns_zero_on_success(monkeypatch):
    monkeypatch.setattr(setup, "main", lambda: None)
    assert setup._cli() == 0


def test_cli_returns_one_on_keyboard_interrupt(monkeypatch):
    def raise_interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr(setup, "main", raise_interrupt)
    assert setup._cli() == 1
