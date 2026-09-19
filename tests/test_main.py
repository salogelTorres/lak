from unittest.mock import MagicMock

import app.main as main_module
from app.router import OllamaRouter


def test_main_wires_everything_and_polls(monkeypatch):
    fake_config = MagicMock(agent_name="Rex", llm_backend="ollama", router_model="")
    fake_llm_client = MagicMock()
    fake_app = MagicMock()

    monkeypatch.setattr(main_module.Config, "load", MagicMock(return_value=fake_config))
    build_llm_client = MagicMock(return_value=fake_llm_client)
    monkeypatch.setattr(main_module, "build_llm_client", build_llm_client)
    build_application = MagicMock(return_value=fake_app)
    monkeypatch.setattr(main_module, "build_application", build_application)

    main_module.main()

    build_llm_client.assert_called_once_with(fake_config)
    build_application.assert_called_once_with(fake_config, fake_llm_client, None)
    fake_app.run_polling.assert_called_once()


def test_main_builds_a_router_when_router_model_is_set(monkeypatch):
    fake_config = MagicMock(
        agent_name="Rex", llm_backend="ollama", router_model="qwen3.5:4b", ollama_base_url="http://ollama:11434"
    )
    monkeypatch.setattr(main_module.Config, "load", MagicMock(return_value=fake_config))
    monkeypatch.setattr(main_module, "build_llm_client", MagicMock())
    build_application = MagicMock()
    monkeypatch.setattr(main_module, "build_application", build_application)

    main_module.main()

    router = build_application.call_args.args[2]
    assert isinstance(router, OllamaRouter)
    assert router.base_url == "http://ollama:11434"
    assert router.model == "qwen3.5:4b"


def test_main_skips_router_for_cloud_backend_even_with_router_model_set(monkeypatch):
    fake_config = MagicMock(agent_name="Rex", llm_backend="cloud", router_model="qwen3.5:4b")
    monkeypatch.setattr(main_module.Config, "load", MagicMock(return_value=fake_config))
    monkeypatch.setattr(main_module, "build_llm_client", MagicMock())
    build_application = MagicMock()
    monkeypatch.setattr(main_module, "build_application", build_application)

    main_module.main()

    assert build_application.call_args.args[2] is None
