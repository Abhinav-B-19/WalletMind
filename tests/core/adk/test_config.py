from __future__ import annotations

from backend.app.adk.config import AdkRuntimeSettings


def test_adk_settings_from_environment_defaults(monkeypatch):
    monkeypatch.delenv("WALLETMIND_ADK_APP_NAME", raising=False)
    monkeypatch.delenv("WALLETMIND_ADK_WORKFLOW_NAME", raising=False)
    monkeypatch.delenv("WALLETMIND_ADK_DEFAULT_USER", raising=False)
    monkeypatch.delenv("WALLETMIND_ADK_SESSION_PREFIX", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    settings = AdkRuntimeSettings.from_environment()

    assert settings.app_name == "walletmind"
    assert settings.root_workflow_name == "walletmind_root_workflow"
    assert settings.default_user_id == "walletmind-system"
    assert settings.default_session_prefix == "wm-session"
    assert settings.model_name == "gemini-2.5-flash"


def test_adk_settings_from_environment_overrides(monkeypatch):
    monkeypatch.setenv("WALLETMIND_ADK_APP_NAME", "wm-prod")
    monkeypatch.setenv("WALLETMIND_ADK_WORKFLOW_NAME", "wm_workflow")
    monkeypatch.setenv("WALLETMIND_ADK_DEFAULT_USER", "system-user")
    monkeypatch.setenv("WALLETMIND_ADK_SESSION_PREFIX", "session")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-flash-latest")

    settings = AdkRuntimeSettings.from_environment()

    assert settings.app_name == "wm-prod"
    assert settings.root_workflow_name == "wm_workflow"
    assert settings.default_user_id == "system-user"
    assert settings.default_session_prefix == "session"
    assert settings.model_name == "gemini-flash-latest"
