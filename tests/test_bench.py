from unittest.mock import MagicMock

import bench


def test_parse_args_splits_models_from_passthrough():
    models, passthrough = bench.parse_args(["qwen3:0.6b", "qwen3:4b", "--", "--attempts", "5"])

    assert models == ["qwen3:0.6b", "qwen3:4b"]
    assert passthrough == ["--attempts", "5"]


def test_parse_args_without_double_dash():
    models, passthrough = bench.parse_args(["qwen3:8b"])

    assert models == ["qwen3:8b"]
    assert passthrough == []


def test_parse_args_double_dash_with_nothing_after():
    models, passthrough = bench.parse_args(["qwen3:8b", "--"])

    assert models == ["qwen3:8b"]
    assert passthrough == []


def test_parse_args_empty():
    assert bench.parse_args([]) == ([], [])


OLLAMA_LIST_OUTPUT = (
    "NAME              ID              SIZE      MODIFIED\n"
    "qwen3:8b          500a1f067a9f    6.0 GB    2 hours ago\n"
    "llama3:latest     abc123          4.7 GB    3 days ago\n"
    "\n"
)


def test_installed_models_parses_ollama_list(monkeypatch):
    monkeypatch.setattr(
        bench.subprocess, "run", MagicMock(return_value=MagicMock(returncode=0, stdout=OLLAMA_LIST_OUTPUT))
    )

    names = bench.installed_models()

    assert "qwen3:8b" in names
    assert "llama3:latest" in names
    assert "llama3" in names  # :latest suffix stripped too


def test_installed_models_empty_on_failure(monkeypatch):
    monkeypatch.setattr(bench.subprocess, "run", MagicMock(return_value=MagicMock(returncode=1, stdout="")))

    assert bench.installed_models() == set()


def test_main_prints_usage_without_models(capsys):
    assert bench.main([]) == 2
    assert "Usage:" in capsys.readouterr().out


def test_main_stops_if_docker_is_not_running(monkeypatch):
    monkeypatch.setattr(bench, "ensure_docker_running", MagicMock(return_value=False))

    assert bench.main(["qwen3:8b"]) == 1


def test_main_pulls_missing_models_then_runs_the_eval(monkeypatch):
    monkeypatch.setattr(bench, "ensure_docker_running", MagicMock(return_value=True))
    monkeypatch.setattr(bench, "installed_models", MagicMock(return_value={"qwen3:8b"}))
    pull_mock = MagicMock(return_value=True)
    monkeypatch.setattr(bench, "pull_ollama_model", pull_mock)
    run_mock = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(bench.subprocess, "run", run_mock)

    exit_code = bench.main(["qwen3:8b", "qwen3:4b", "--", "--attempts", "5"])

    assert exit_code == 0
    pull_mock.assert_called_once_with("qwen3:4b")  # qwen3:8b already installed, not re-pulled
    run_mock.assert_called_once_with(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "bot",
            "python",
            "-m",
            "evals.router_bench",
            "--models",
            "qwen3:8b",
            "qwen3:4b",
            "--attempts",
            "5",
        ],
        cwd=bench.ROOT,
        check=False,
    )


def test_main_stops_if_a_pull_fails(monkeypatch):
    monkeypatch.setattr(bench, "ensure_docker_running", MagicMock(return_value=True))
    monkeypatch.setattr(bench, "installed_models", MagicMock(return_value=set()))
    monkeypatch.setattr(bench, "pull_ollama_model", MagicMock(return_value=False))
    run_mock = MagicMock()
    monkeypatch.setattr(bench.subprocess, "run", run_mock)

    assert bench.main(["qwen3:4b"]) == 1
    run_mock.assert_not_called()
