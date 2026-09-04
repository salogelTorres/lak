from unittest.mock import MagicMock

import pytest

import setup
import update


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    return tmp_path


def test_ensure_template_remote_adds_when_missing(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if args == ["git", "remote"]:
            return MagicMock(stdout="origin\n", returncode=0)
        return MagicMock(returncode=0)

    monkeypatch.setattr(update.subprocess, "run", fake_run)

    update.ensure_template_remote()

    assert ["git", "remote", "add", "template", update.TEMPLATE_URL] in calls


def test_ensure_template_remote_noop_when_already_present(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return MagicMock(stdout="origin\ntemplate\n", returncode=0)

    monkeypatch.setattr(update.subprocess, "run", fake_run)

    update.ensure_template_remote()

    assert all(call[:3] != ["git", "remote", "add"] for call in calls)


def test_fetch_and_merge_success(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return MagicMock(returncode=0)

    monkeypatch.setattr(update.subprocess, "run", fake_run)

    assert update.fetch_and_merge() is True
    assert calls == [
        ["git", "fetch", "template"],
        ["git", "merge", "template/main", "--no-edit"],
    ]


def test_fetch_and_merge_reports_fetch_failure(monkeypatch, capsys):
    monkeypatch.setattr(update.subprocess, "run", lambda args, **kw: MagicMock(returncode=1))

    assert update.fetch_and_merge() is False
    assert "Could not fetch" in capsys.readouterr().out


def test_fetch_and_merge_reports_merge_conflict(monkeypatch, capsys):
    def fake_run(args, **kwargs):
        if "fetch" in args:
            return MagicMock(returncode=0)
        return MagicMock(returncode=1)

    monkeypatch.setattr(update.subprocess, "run", fake_run)

    assert update.fetch_and_merge() is False
    assert "Merge conflict" in capsys.readouterr().out


def test_fill_in_new_env_keys_adds_missing_and_preserves_existing(tmp_path, monkeypatch):
    env_example = tmp_path / ".env.example"
    env_example.write_text("A=1\nB=2\nC=3\n", encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text("A=custom\nB=2\n", encoding="utf-8")

    monkeypatch.setattr(setup, "ENV_EXAMPLE", env_example)
    monkeypatch.setattr(setup, "ENV_FILE", env_file)

    added = update.fill_in_new_env_keys()

    assert added == ["C"]
    content = env_file.read_text(encoding="utf-8")
    assert content.count("A=") == 1
    assert "A=custom" in content
    assert "C=3" in content


def test_fill_in_new_env_keys_noop_when_nothing_missing(tmp_path, monkeypatch):
    env_example = tmp_path / ".env.example"
    env_example.write_text("A=1\n", encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text("A=custom\n", encoding="utf-8")

    monkeypatch.setattr(setup, "ENV_EXAMPLE", env_example)
    monkeypatch.setattr(setup, "ENV_FILE", env_file)

    assert update.fill_in_new_env_keys() == []
    assert env_file.read_text(encoding="utf-8") == "A=custom\n"


def test_fill_in_new_env_keys_noop_without_env_file(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "ENV_FILE", tmp_path / ".env")
    assert update.fill_in_new_env_keys() == []


def test_main_fails_without_git_repo(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(setup, "ROOT", tmp_path)

    assert update.main() == 1
    assert "doesn't look like a git repository" in capsys.readouterr().out


def test_main_stops_when_fetch_and_merge_fails(fake_repo, monkeypatch):
    monkeypatch.setattr(update, "ensure_template_remote", MagicMock())
    monkeypatch.setattr(update, "fetch_and_merge", MagicMock(return_value=False))
    run_mock = MagicMock()
    monkeypatch.setattr(update.subprocess, "run", run_mock)

    assert update.main() == 1
    run_mock.assert_not_called()


def test_main_full_success_flow_reports_new_keys_and_gpu(fake_repo, monkeypatch, capsys):
    monkeypatch.setattr(update, "ensure_template_remote", MagicMock())
    monkeypatch.setattr(update, "fetch_and_merge", MagicMock(return_value=True))
    monkeypatch.setattr(update, "fill_in_new_env_keys", MagicMock(return_value=["TZ", "WHISPER_MODEL"]))
    monkeypatch.setattr(setup, "ensure_system_prompt", MagicMock())
    monkeypatch.setattr(setup, "ensure_gpu_override", MagicMock(return_value=True))
    run_mock = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(update.subprocess, "run", run_mock)

    assert update.main() == 0

    run_mock.assert_called_once_with(
        ["docker", "compose", "up", "-d", "--build"], cwd=setup.ROOT, check=False
    )
    out = capsys.readouterr().out
    assert "TZ, WHISPER_MODEL" in out
    assert "NVIDIA GPU detected" in out
    assert "Done." in out


def test_main_success_without_new_keys_or_gpu_skips_those_messages(fake_repo, monkeypatch, capsys):
    monkeypatch.setattr(update, "ensure_template_remote", MagicMock())
    monkeypatch.setattr(update, "fetch_and_merge", MagicMock(return_value=True))
    monkeypatch.setattr(update, "fill_in_new_env_keys", MagicMock(return_value=[]))
    monkeypatch.setattr(setup, "ensure_system_prompt", MagicMock())
    monkeypatch.setattr(setup, "ensure_gpu_override", MagicMock(return_value=False))
    monkeypatch.setattr(update.subprocess, "run", MagicMock(return_value=MagicMock(returncode=0)))

    assert update.main() == 0

    out = capsys.readouterr().out
    assert "New .env setting" not in out
    assert "NVIDIA GPU detected" not in out


def test_cli_returns_zero_on_success(monkeypatch):
    monkeypatch.setattr(update, "main", lambda: 0)
    assert update._cli() == 0


def test_cli_returns_one_on_keyboard_interrupt(monkeypatch):
    def raise_interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr(update, "main", raise_interrupt)
    assert update._cli() == 1
