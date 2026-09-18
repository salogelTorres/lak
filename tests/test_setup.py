from unittest.mock import MagicMock

import pytest

import setup

ENV_EXAMPLE_CONTENT = """\
TELEGRAM_BOT_TOKEN=
ALLOWED_USER_IDS=
AGENT_NAME=Assistant
SYSTEM_PROMPT_FILE=app/prompts/system_prompt.txt
TZ=UTC
LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
CLOUD_API_BASE_URL=https://api.openai.com/v1
CLOUD_API_KEY=
CLOUD_MODEL=gpt-4o-mini
"""


GPU_OVERRIDE_CONTENT = "services:\n  ollama:\n    deploy:\n      resources: {}\n"


def which_only_docker(name: str) -> str | None:
    """Default `shutil.which` stand-in: docker is on PATH, nothing else is
    (in particular, no nvidia-smi — no GPU detected)."""
    return "/usr/bin/docker" if name == "docker" else None


@pytest.fixture
def env_paths(tmp_path, monkeypatch):
    env_example = tmp_path / ".env.example"
    env_example.write_text(ENV_EXAMPLE_CONTENT, encoding="utf-8")
    env_file = tmp_path / ".env"

    prompt_dir = tmp_path / "app" / "prompts"
    prompt_dir.mkdir(parents=True)
    prompt_example = prompt_dir / "system_prompt.txt.example"
    prompt_example.write_text("You are {{AGENT_NAME}}.", encoding="utf-8")
    prompt_file = prompt_dir / "system_prompt.txt"

    gpu_override_example = tmp_path / "docker-compose.override.yml.example"
    gpu_override_example.write_text(GPU_OVERRIDE_CONTENT, encoding="utf-8")
    gpu_override_file = tmp_path / "docker-compose.override.yml"

    monkeypatch.setattr(setup, "ENV_EXAMPLE", env_example)
    monkeypatch.setattr(setup, "ENV_FILE", env_file)
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "SYSTEM_PROMPT_EXAMPLE", prompt_example)
    monkeypatch.setattr(setup, "SYSTEM_PROMPT_FILE", prompt_file)
    monkeypatch.setattr(setup, "GPU_OVERRIDE_EXAMPLE", gpu_override_example)
    monkeypatch.setattr(setup, "GPU_OVERRIDE_FILE", gpu_override_file)
    monkeypatch.setattr(setup.shutil, "which", which_only_docker)
    return env_example, env_file, prompt_file, gpu_override_file


def env_dict(env_file) -> dict[str, str]:
    result = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        result[key] = value
    return result


def scripted_input(monkeypatch, responses):
    it = iter(responses)
    monkeypatch.setattr("builtins.input", lambda prompt: next(it))


def test_parse_env_example_skips_comments_and_blanks(tmp_path, monkeypatch):
    env_example = tmp_path / ".env.example"
    env_example.write_text("# a comment\n\nTELEGRAM_BOT_TOKEN=\nAGENT_NAME=Assistant\n", encoding="utf-8")
    monkeypatch.setattr(setup, "ENV_EXAMPLE", env_example)

    assert setup.parse_env_example() == [("TELEGRAM_BOT_TOKEN", ""), ("AGENT_NAME", "Assistant")]


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


def test_ask_llm_backend_accepts_explicit_value(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "cloud")
    assert setup.ask_llm_backend("ollama") == "cloud"


def test_ask_llm_backend_accepts_local_alias_for_ollama(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "local")
    assert setup.ask_llm_backend("ollama") == "ollama"


def test_ask_llm_backend_falls_back_to_default_on_empty_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert setup.ask_llm_backend("cloud") == "cloud"


def test_ask_llm_backend_ignores_bogus_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert setup.ask_llm_backend("not-a-real-backend") == "ollama"


def test_ask_llm_backend_reprompts_on_invalid_value(monkeypatch, capsys):
    scripted_input(monkeypatch, ["nope", "local"])
    assert setup.ask_llm_backend("ollama") == "ollama"
    assert "Please type 'local' or 'cloud'" in capsys.readouterr().out


def test_ask_enabled_tools_uses_input_value(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "search_web")
    assert setup.ask_enabled_tools("") == "search_web"


def test_ask_enabled_tools_falls_back_to_default_on_empty_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert setup.ask_enabled_tools("search_web") == "search_web"


def test_ask_enabled_tools_drops_unknown_names(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "search_web, bogus_tool")
    assert setup.ask_enabled_tools("") == "search_web"


def test_ask_enabled_tools_empty_input_and_default_disables_all(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert setup.ask_enabled_tools("") == ""


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


def test_apply_personality_appends_when_given(env_paths):
    setup.SYSTEM_PROMPT_FILE.write_text("base prompt", encoding="utf-8")
    setup.apply_personality("Be extra playful.")
    content = setup.SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    assert content == "base prompt\nBe extra playful.\n"


def test_apply_personality_noop_when_blank(env_paths):
    setup.SYSTEM_PROMPT_FILE.write_text("base prompt", encoding="utf-8")
    setup.apply_personality("")
    assert setup.SYSTEM_PROMPT_FILE.read_text(encoding="utf-8") == "base prompt"


def test_apply_personality_noop_when_file_missing(env_paths):
    setup.apply_personality("Be extra playful.")
    assert not setup.SYSTEM_PROMPT_FILE.exists()


def test_pull_ollama_model_succeeds_on_first_try(monkeypatch):
    run_mock = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(setup.subprocess, "run", run_mock)
    sleep_mock = MagicMock()
    monkeypatch.setattr(setup.time, "sleep", sleep_mock)

    assert setup.pull_ollama_model("llama3") is True
    run_mock.assert_called_once_with(
        ["docker", "compose", "exec", "-T", "ollama", "ollama", "pull", "llama3"],
        cwd=setup.ROOT,
        check=False,
    )
    sleep_mock.assert_not_called()


def test_pull_ollama_model_retries_then_succeeds(monkeypatch):
    run_mock = MagicMock(
        side_effect=[MagicMock(returncode=1), MagicMock(returncode=1), MagicMock(returncode=0)]
    )
    monkeypatch.setattr(setup.subprocess, "run", run_mock)
    sleep_mock = MagicMock()
    monkeypatch.setattr(setup.time, "sleep", sleep_mock)

    assert setup.pull_ollama_model("llama3", retries=5, delay_seconds=0) is True
    assert run_mock.call_count == 3
    assert sleep_mock.call_count == 2


def test_pull_ollama_model_gives_up_after_retries(monkeypatch, capsys):
    run_mock = MagicMock(return_value=MagicMock(returncode=1))
    monkeypatch.setattr(setup.subprocess, "run", run_mock)
    monkeypatch.setattr(setup.time, "sleep", MagicMock())

    assert setup.pull_ollama_model("llama3", retries=2, delay_seconds=0) is False
    assert run_mock.call_count == 2
    assert "Could not pull the model automatically" in capsys.readouterr().out


def test_detect_nvidia_gpu_true_when_nvidia_smi_present(monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None)
    assert setup.detect_nvidia_gpu() is True


def test_detect_nvidia_gpu_false_when_absent(monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    assert setup.detect_nvidia_gpu() is False


def test_ensure_gpu_override_creates_file_when_gpu_detected(env_paths, monkeypatch):
    *_, gpu_override_file = env_paths
    monkeypatch.setattr(setup, "detect_nvidia_gpu", lambda: True)

    assert setup.ensure_gpu_override() is True
    assert gpu_override_file.read_text(encoding="utf-8") == GPU_OVERRIDE_CONTENT


def test_ensure_gpu_override_noop_without_gpu(env_paths, monkeypatch):
    *_, gpu_override_file = env_paths
    monkeypatch.setattr(setup, "detect_nvidia_gpu", lambda: False)

    assert setup.ensure_gpu_override() is False
    assert not gpu_override_file.exists()


def test_ensure_gpu_override_does_not_overwrite_existing_file(env_paths, monkeypatch):
    *_, gpu_override_file = env_paths
    gpu_override_file.write_text("custom override", encoding="utf-8")
    monkeypatch.setattr(setup, "detect_nvidia_gpu", lambda: True)

    assert setup.ensure_gpu_override() is False
    assert gpu_override_file.read_text(encoding="utf-8") == "custom override"


def test_ensure_gpu_override_noop_without_example(env_paths, monkeypatch):
    setup.GPU_OVERRIDE_EXAMPLE.unlink()
    monkeypatch.setattr(setup, "detect_nvidia_gpu", lambda: True)

    assert setup.ensure_gpu_override() is False


def test_docker_is_running_true_on_returncode_zero(monkeypatch):
    monkeypatch.setattr(setup.subprocess, "run", MagicMock(return_value=MagicMock(returncode=0)))
    assert setup.docker_is_running() is True


def test_docker_is_running_false_on_nonzero_returncode(monkeypatch):
    monkeypatch.setattr(setup.subprocess, "run", MagicMock(return_value=MagicMock(returncode=1)))
    assert setup.docker_is_running() is False


def test_start_docker_daemon_windows_launches_existing_candidate(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Windows")
    monkeypatch.setattr(setup.Path, "exists", lambda self: True)
    popen_mock = MagicMock()
    monkeypatch.setattr(setup.subprocess, "Popen", popen_mock)

    assert setup._start_docker_daemon() is True
    popen_mock.assert_called_once()


def test_start_docker_daemon_windows_no_candidate_found(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Windows")
    monkeypatch.setattr(setup.Path, "exists", lambda self: False)

    assert setup._start_docker_daemon() is False


def test_start_docker_daemon_darwin_uses_open(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/bin/open" if name == "open" else None)
    run_mock = MagicMock()
    monkeypatch.setattr(setup.subprocess, "run", run_mock)

    assert setup._start_docker_daemon() is True
    run_mock.assert_called_once_with(["open", "-a", "Docker"], check=False)


def test_start_docker_daemon_darwin_without_open(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)

    assert setup._start_docker_daemon() is False


def test_start_docker_daemon_linux_uses_systemctl(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/bin/systemctl" if name == "systemctl" else None)
    monkeypatch.setattr(setup.subprocess, "run", MagicMock(return_value=MagicMock(returncode=0)))

    assert setup._start_docker_daemon() is True


def test_start_docker_daemon_linux_systemctl_fails_falls_back_to_service(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        setup.shutil, "which", lambda name: f"/usr/bin/{name}" if name in ("systemctl", "service") else None
    )

    def fake_run(args, **kwargs):
        return MagicMock(returncode=1 if args[:2] == ["systemctl", "start"] else 0)

    monkeypatch.setattr(setup.subprocess, "run", fake_run)

    assert setup._start_docker_daemon() is True


def test_start_docker_daemon_linux_without_systemctl_or_service(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)

    assert setup._start_docker_daemon() is False


def test_start_docker_daemon_unknown_platform(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Plan9")
    assert setup._start_docker_daemon() is False


def test_ensure_docker_running_already_running(monkeypatch):
    monkeypatch.setattr(setup, "docker_is_running", lambda: True)
    assert setup.ensure_docker_running() is True


def test_ensure_docker_running_cannot_start(monkeypatch, capsys):
    monkeypatch.setattr(setup, "docker_is_running", lambda: False)
    monkeypatch.setattr(setup, "_start_docker_daemon", lambda: False)

    assert setup.ensure_docker_running() is False
    assert "Could not start Docker automatically" in capsys.readouterr().out


def test_ensure_docker_running_starts_and_becomes_ready(monkeypatch):
    monkeypatch.setattr(setup, "_start_docker_daemon", lambda: True)
    monkeypatch.setattr(setup.time, "sleep", MagicMock())
    calls = {"n": 0}

    def fake_is_running():
        calls["n"] += 1
        return calls["n"] >= 2  # not running yet on the initial check, ready on the first poll

    monkeypatch.setattr(setup, "docker_is_running", fake_is_running)

    assert setup.ensure_docker_running(timeout_seconds=10, poll_seconds=1) is True


def test_ensure_docker_running_times_out(monkeypatch, capsys):
    monkeypatch.setattr(setup, "_start_docker_daemon", lambda: True)
    monkeypatch.setattr(setup, "docker_is_running", lambda: False)
    monkeypatch.setattr(setup.time, "sleep", MagicMock())

    assert setup.ensure_docker_running(timeout_seconds=3, poll_seconds=1) is False
    assert "did not become ready" in capsys.readouterr().out


def test_main_declines_overwrite(env_paths, monkeypatch, capsys):
    _, env_file, _, _ = env_paths
    env_file.write_text("EXISTING=1\n", encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    setup.main()

    assert env_file.read_text(encoding="utf-8") == "EXISTING=1\n"
    assert "Cancelled" in capsys.readouterr().out


def test_main_ollama_backend_without_docker(env_paths, monkeypatch, capsys):
    _, env_file, prompt_file, _ = env_paths
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    scripted_input(
        monkeypatch,
        [
            "my-token",  # TELEGRAM_BOT_TOKEN
            "",  # ALLOWED_USER_IDS (default)
            "Rex",  # AGENT_NAME
            "Europe/Madrid",  # TZ
            "",  # LLM_BACKEND (default: ollama)
            "qwen3:8b",  # OLLAMA_MODEL
            "",  # ENABLED_TOOLS (default: none)
            "",  # personality (skip)
        ],
    )

    setup.main()

    values = env_dict(env_file)
    assert values["TELEGRAM_BOT_TOKEN"] == "my-token"
    assert values["AGENT_NAME"] == "Rex"
    assert values["TZ"] == "Europe/Madrid"
    assert values["LLM_BACKEND"] == "ollama"
    assert values["OLLAMA_MODEL"] == "qwen3:8b"
    assert values["SYSTEM_PROMPT_FILE"] == "app/prompts/system_prompt.txt"
    assert values["CLOUD_API_KEY"] == ""
    assert prompt_file.read_text(encoding="utf-8") == "You are {{AGENT_NAME}}."
    assert "Docker was not found" in capsys.readouterr().out


def test_main_cloud_backend_with_personality_and_docker_launch(env_paths, monkeypatch, capsys):
    _, env_file, prompt_file, gpu_override_file = env_paths
    # even with a GPU present, the cloud backend never checks for one
    monkeypatch.setattr(setup, "detect_nvidia_gpu", lambda: True)
    # returncode=0 so docker_is_running() reports Docker as already up,
    # short-circuiting ensure_docker_running() before it would otherwise
    # try to actually launch Docker Desktop on the host.
    run_mock = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(setup.subprocess, "run", run_mock)
    pull_mock = MagicMock()
    monkeypatch.setattr(setup, "pull_ollama_model", pull_mock)
    scripted_input(
        monkeypatch,
        [
            "my-token",
            "123,456",
            "Rex2",
            "",  # TZ (default: UTC)
            "cloud",
            "sk-key",
            "gpt-4o",
            "search_web",  # ENABLED_TOOLS
            "Be extra playful.",
            "",  # launch docker (default: yes)
        ],
    )

    setup.main()

    values = env_dict(env_file)
    assert values["TZ"] == "UTC"
    assert values["LLM_BACKEND"] == "cloud"
    assert values["CLOUD_API_KEY"] == "sk-key"
    assert values["CLOUD_MODEL"] == "gpt-4o"
    assert values["ENABLED_TOOLS"] == "search_web"
    assert values["OLLAMA_MODEL"] == "llama3"  # untouched default
    assert prompt_file.read_text(encoding="utf-8") == "You are {{AGENT_NAME}}.\nBe extra playful.\n"

    assert run_mock.call_args_list[-1] == (
        (["docker", "compose", "up", "-d", "--build"],),
        {"cwd": setup.ROOT, "check": False},
    )
    pull_mock.assert_not_called()
    assert not gpu_override_file.exists()
    assert "Agent is up" in capsys.readouterr().out


def test_main_ollama_backend_with_docker_launch_pulls_model(env_paths, monkeypatch, capsys):
    _, env_file, _, gpu_override_file = env_paths
    # returncode=0 so docker_is_running() reports Docker as already up,
    # short-circuiting ensure_docker_running() before it would otherwise
    # try to actually launch Docker Desktop on the host.
    run_mock = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(setup.subprocess, "run", run_mock)
    pull_mock = MagicMock(return_value=True)
    monkeypatch.setattr(setup, "pull_ollama_model", pull_mock)
    scripted_input(monkeypatch, ["my-token", "", "Rex", "", "local", "qwen3:8b", "", "", ""])

    setup.main()

    values = env_dict(env_file)
    assert values["LLM_BACKEND"] == "ollama"
    assert values["OLLAMA_MODEL"] == "qwen3:8b"
    assert run_mock.call_args_list[-1] == (
        (["docker", "compose", "up", "-d", "--build"],),
        {"cwd": setup.ROOT, "check": False},
    )
    pull_mock.assert_called_once_with("qwen3:8b")
    # no GPU in this fixture (which_only_docker), so no override file
    assert not gpu_override_file.exists()
    assert "Agent is up" in capsys.readouterr().out


def test_main_ollama_backend_with_gpu_enables_override(env_paths, monkeypatch, capsys):
    _, env_file, _, gpu_override_file = env_paths
    monkeypatch.setattr(setup, "detect_nvidia_gpu", lambda: True)
    # returncode=0 so docker_is_running() reports Docker as already up,
    # short-circuiting ensure_docker_running() before it would otherwise
    # try to actually launch Docker Desktop on the host.
    monkeypatch.setattr(setup.subprocess, "run", MagicMock(return_value=MagicMock(returncode=0)))
    monkeypatch.setattr(setup, "pull_ollama_model", MagicMock(return_value=True))
    scripted_input(monkeypatch, ["my-token", "", "Rex", "", "local", "qwen3:8b", "", "", ""])

    setup.main()

    assert gpu_override_file.read_text(encoding="utf-8") == GPU_OVERRIDE_CONTENT
    assert "NVIDIA GPU detected" in capsys.readouterr().out


def test_main_declines_docker_launch(env_paths, monkeypatch, capsys):
    _, env_file, _, gpu_override_file = env_paths
    run_mock = MagicMock()
    monkeypatch.setattr(setup.subprocess, "run", run_mock)
    scripted_input(monkeypatch, ["my-token", "", "Rex", "", "", "llama3", "", "", "n"])

    setup.main()

    run_mock.assert_not_called()
    assert "When you're ready" in capsys.readouterr().out


def test_main_reprompts_on_invalid_llm_backend_before_continuing(env_paths, monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    scripted_input(
        monkeypatch,
        ["my-token", "", "Rex", "", "nope", "local", "llama3", "", ""],
    )

    setup.main()  # must not raise


def test_main_accepts_local_as_ollama_alias(env_paths, monkeypatch):
    _, env_file, _, _ = env_paths
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    scripted_input(monkeypatch, ["my-token", "", "Rex", "", "local", "llama3", "", ""])

    setup.main()

    assert env_dict(env_file)["LLM_BACKEND"] == "ollama"


def test_cli_returns_zero_on_success(monkeypatch):
    monkeypatch.setattr(setup, "main", lambda: None)
    assert setup._cli() == 0


def test_cli_returns_one_on_keyboard_interrupt(monkeypatch):
    def raise_interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr(setup, "main", raise_interrupt)
    assert setup._cli() == 1
