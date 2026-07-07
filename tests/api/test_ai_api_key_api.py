from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.main import create_app


def _client_with_validator(validator) -> TestClient:
    app = create_app()
    app.state.gemini_api_key_validator = validator
    return TestClient(app)


def _client_without_validator() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_set_status_delete_api_key_flow() -> None:
    client = _client_with_validator(lambda key: key.startswith("AIza"))

    set_response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-session-key"},
    )
    assert set_response.status_code == 200
    assert set_response.json() == {"success": True}

    status_response = client.get("/api/v1/ai/api-key/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["configured"] is True
    assert status_payload["source"] == "session"
    assert status_payload["model"] == "gemini-2.5-flash"
    assert status_payload["masked_key"].startswith("AIza")
    assert status_payload["last_validated"] is not None

    reveal_response = client.get("/api/v1/ai/api-key")
    assert reveal_response.status_code == 200
    reveal_payload = reveal_response.json()
    assert reveal_payload["configured"] is True
    assert reveal_payload["source"] == "session"
    assert reveal_payload["api_key"] == "AIza-valid-session-key"

    delete_response = client.delete("/api/v1/ai/api-key")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"success": True}

    status_after_delete = client.get("/api/v1/ai/api-key/status")
    assert status_after_delete.status_code == 200
    assert status_after_delete.json()["configured"] is False


def test_set_api_key_rejects_unsupported_credentials() -> None:
    client = _client_with_validator(lambda _key: True)

    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "ZZ-not-a-supported-gemini-credential"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "AI_KEY_INVALID_FORMAT"
    assert payload["message"] == "This doesn't appear to be a supported Gemini credential."
    assert payload["details"]["supported_prefixes"] == ["AIza", "AQ"]


def test_set_api_key_accepts_aq_auth_key() -> None:
    client = _client_with_validator(lambda key: key.startswith("AQ"))

    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AQ-valid-auth-key-12345"},
    )

    assert response.status_code == 200
    reveal_response = client.get("/api/v1/ai/api-key")
    assert reveal_response.status_code == 200
    assert reveal_response.json()["api_key"] == "AQ-valid-auth-key-12345"


def test_set_api_key_invalid_format_skips_sdk_validation(monkeypatch) -> None:
    from backend.app.services.ai.gemini_client import GeminiClient

    calls = {"count": 0}

    def _should_not_run(_self) -> None:
        calls["count"] += 1
        raise AssertionError("SDK validation should not run for invalid format")

    monkeypatch.setattr(GeminiClient, "validate_api_key_lightweight", _should_not_run)

    client = _client_without_validator()
    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "ZZ-token-should-fail-format-gate"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "AI_KEY_INVALID_FORMAT"
    assert calls["count"] == 0


def test_set_api_key_invalid_returns_validation_error() -> None:
    client = _client_with_validator(lambda _key: False)

    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-invalid-but-format-valid-123456"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["code"] == "AI_KEY_INVALID"
    assert payload["message"] == "Unable to validate Gemini API key."


def test_set_api_key_accepts_quoted_aiza_keys() -> None:
    client = _client_with_validator(lambda key: key.startswith("AIza"))

    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": '  "AIza-valid-quoted-session-key-123456"  '},
    )

    assert response.status_code == 200
    reveal_response = client.get("/api/v1/ai/api-key")
    assert reveal_response.status_code == 200
    assert reveal_response.json()["api_key"] == "AIza-valid-quoted-session-key-123456"


def test_short_but_prefixed_key_is_not_rejected_as_format() -> None:
    client = _client_with_validator(lambda _key: False)

    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-short"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "AI_KEY_INVALID"


def test_set_api_key_malformed_format_returns_validation_error() -> None:
    client = _client_without_validator()

    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "not-a-gemini-key"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "AI_KEY_INVALID_FORMAT"
    assert payload["message"] == "This doesn't appear to be a supported Gemini credential."
    assert payload["details"]["supported_prefixes"] == ["AIza", "AQ"]


def test_set_api_key_empty_returns_validation_error() -> None:
    client = _client_without_validator()

    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "   "},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "AI_KEY_INVALID_FORMAT"
    assert payload["message"] == "This doesn't appear to be a supported Gemini credential."
    assert payload["details"]["supported_prefixes"] == ["AIza", "AQ"]


def test_logout_clears_session_key() -> None:
    client = _client_with_validator(lambda key: key.startswith("AIza"))

    set_response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-session-key"},
    )
    assert set_response.status_code == 200

    logout_response = client.post("/api/v1/users/logout")
    assert logout_response.status_code == 200

    status_response = client.get("/api/v1/ai/api-key/status")
    assert status_response.status_code == 200
    assert status_response.json()["configured"] is False


def test_developer_fallback_when_enabled(monkeypatch) -> None:
    from backend.app.services.ai import api_key_provider

    monkeypatch.setattr(
        api_key_provider,
        "_settings",
        lambda: SimpleNamespace(
            developer_mode=True,
            gemini_api_key="AIza-developer-fallback",
            gemini_model="gemini-2.5-flash",
            session_max_age_seconds=60,
        ),
    )

    client = _client_with_validator(lambda key: key.startswith("AIza"))

    status_response = client.get("/api/v1/ai/api-key/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["configured"] is True
    assert status_payload["source"] == "developer"
    assert status_payload["masked_key"] is None

    reveal_response = client.get("/api/v1/ai/api-key")
    assert reveal_response.status_code == 404


def test_ai_health_uses_session_key_source() -> None:
    client = _client_with_validator(lambda key: key.startswith("AIza"))

    set_response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-session-key"},
    )
    assert set_response.status_code == 200

    health_response = client.get("/api/v1/ai/health")
    assert health_response.status_code == 200

    payload = health_response.json()
    assert payload["success"] is True
    assert payload["data"]["configured"] is True
    assert payload["data"]["source"] == "session"


def test_set_api_key_network_timeout_returns_friendly_message(monkeypatch) -> None:
    from backend.app.services.ai.gemini_client import GeminiClient

    monkeypatch.setattr(
        GeminiClient,
        "validate_api_key_lightweight",
        lambda _self: (_ for _ in ()).throw(TimeoutError("timeout")),
    )

    client = _client_without_validator()
    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-format-for-timeout-check"},
    )

    assert response.status_code == 502
    payload = response.json()
    assert payload["code"] == "AI_KEY_NETWORK_ERROR"
    assert payload["message"] == "Network issue while validating Gemini API key."


def test_set_api_key_sdk_exception_returns_friendly_message(monkeypatch) -> None:
    from backend.app.services.ai.gemini_client import GeminiClient

    monkeypatch.setattr(
        GeminiClient,
        "validate_api_key_lightweight",
        lambda _self: (_ for _ in ()).throw(RuntimeError("permission denied")),
    )

    client = _client_without_validator()
    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-format-for-permission-check"},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["code"] == "AI_KEY_PERMISSION_DENIED"
    assert (
        payload["message"]
        == "Gemini API access was denied. Check API permissions and try again."
    )


def test_set_api_key_unsupported_auth_key_category(monkeypatch) -> None:
    from backend.app.services.ai.gemini_client import GeminiClient

    monkeypatch.setattr(
        GeminiClient,
        "validate_api_key_lightweight",
        lambda _self: (_ for _ in ()).throw(
            RuntimeError("unsupported authorization key type")
        ),
    )

    client = _client_without_validator()
    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AQ-valid-format-but-unsupported"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "AI_KEY_UNSUPPORTED_AUTH_KEY"


def test_set_api_key_sdk_incompatible_category(monkeypatch) -> None:
    from backend.app.services.ai.gemini_client import GeminiClient

    monkeypatch.setattr(
        GeminiClient,
        "validate_api_key_lightweight",
        lambda _self: (_ for _ in ()).throw(
            RuntimeError("sdk incompatible with auth-key flow")
        ),
    )

    client = _client_without_validator()
    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AQ-valid-format-sdk-check"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["code"] == "AI_KEY_SDK_INCOMPATIBLE"


def test_set_api_key_google_rejection_returns_friendly_message(monkeypatch) -> None:
    from backend.app.services.ai.gemini_client import GeminiClient

    monkeypatch.setattr(
        GeminiClient,
        "validate_api_key_lightweight",
        lambda _self: (_ for _ in ()).throw(RuntimeError("invalid api key")),
    )

    client = _client_without_validator()
    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-format-but-rejected-by-google"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "AI_KEY_INVALID"
    assert payload["message"] == "Gemini API key appears invalid. Please verify and retry."


def test_set_api_key_session_storage_failure_returns_500(monkeypatch) -> None:
    from backend.app.services.ai import api_key_provider

    monkeypatch.setattr(
        api_key_provider,
        "_cache_state",
        lambda _app: (_ for _ in ()).throw(RuntimeError("cache unavailable")),
    )

    app = create_app()
    app.state.gemini_api_key_validator = lambda _key: True
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-session-key"},
    )

    assert response.status_code == 500


def test_invalid_replacement_keeps_previous_valid_key() -> None:
    validation_enabled = {"accept": True}

    def validator(_key: str) -> bool:
        return validation_enabled["accept"]

    client = _client_with_validator(validator)

    set_response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-previous-valid-session-key-12345"},
    )
    assert set_response.status_code == 200

    validation_enabled["accept"] = False
    failed_replace = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-invalid-replacement-key-67890"},
    )
    assert failed_replace.status_code == 422

    reveal_response = client.get("/api/v1/ai/api-key")
    assert reveal_response.status_code == 200
    assert reveal_response.json()["api_key"] == "AIza-previous-valid-session-key-12345"


def test_session_expiry_removes_key() -> None:
    from backend.app.services.ai import api_key_provider

    client = _client_with_validator(lambda _key: True)
    set_response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-session-expiry-key-12345"},
    )
    assert set_response.status_code == 200

    app = client.app
    cache, _lock = api_key_provider._cache_state(app)
    cache.clear()

    status_response = client.get("/api/v1/ai/api-key/status")
    assert status_response.status_code == 200
    assert status_response.json()["configured"] is False

    reveal_response = client.get("/api/v1/ai/api-key")
    assert reveal_response.status_code == 404


def test_status_endpoint_never_returns_key_material() -> None:
    client = _client_with_validator(lambda _key: True)

    set_response = client.post(
        "/api/v1/ai/api-key",
        json={"api_key": "AIza-valid-session-key"},
    )
    assert set_response.status_code == 200

    status_response = client.get("/api/v1/ai/api-key/status")
    assert status_response.status_code == 200
    payload = status_response.json()
    assert "api_key" not in payload
    assert set(payload.keys()) == {
        "configured",
        "masked_key",
        "source",
        "model",
        "last_validated",
    }
