from unittest.mock import MagicMock

import app.main as main_module


def test_main_wires_everything_and_polls(monkeypatch):
    fake_config = MagicMock(agent_name="Rex", llm_backend="ollama")
    fake_llm_client = MagicMock()
    fake_app = MagicMock()

    monkeypatch.setattr(main_module.Config, "load", MagicMock(return_value=fake_config))
    build_llm_client = MagicMock(return_value=fake_llm_client)
    monkeypatch.setattr(main_module, "build_llm_client", build_llm_client)
    build_application = MagicMock(return_value=fake_app)
    monkeypatch.setattr(main_module, "build_application", build_application)

    main_module.main()

    build_llm_client.assert_called_once_with(fake_config)
    build_application.assert_called_once_with(fake_config, fake_llm_client)
    fake_app.run_polling.assert_called_once()
