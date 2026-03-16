import pytest
from src.config import Settings

def test_settings_default():
    settings = Settings()
    assert settings.app_name == "PRism-AI"
    assert settings.app_version == "1.0.0"
    assert settings.llm_provider == "ollama"

def test_settings_to_ui_dict():
    settings = Settings()
    ui_dict = settings.to_ui_dict()
    assert "llm_provider" in ui_dict
    assert "llm_model" in ui_dict
    assert "llm_base_url" in ui_dict

def test_settings_update():
    settings = Settings()
    settings.update({"llm_provider": "openai", "openai_model": "gpt-4o"})
    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-4o"
