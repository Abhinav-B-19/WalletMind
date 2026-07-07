from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_rest_root_landing_returns_judge_friendly_payload() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "WalletMind REST API"
    assert payload["status"] == "running"
    assert payload["documentation"] == "/docs"
    assert payload["health"] == "/health"
    assert payload["openapi"] == "/openapi.json"
    assert isinstance(payload["version"], str)
    assert isinstance(payload["features"], list)
    assert "Coordinator Agent" in payload["features"]


def test_rest_health_landing_returns_running_status() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "WalletMind REST API"
    assert payload["status"] == "running"
    assert isinstance(payload["version"], str)
