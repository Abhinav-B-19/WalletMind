from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.ai.models import AIHealthStatus


class StubAIService:
    def __init__(self, configured: bool, model: str) -> None:
        self._configured = configured
        self._model = model

    def health(self) -> AIHealthStatus:
        status = "healthy" if self._configured else "unhealthy"
        return AIHealthStatus(
            configured=self._configured,
            model=self._model,
            status=status,
        )


def test_ai_health_endpoint_healthy() -> None:
    app = create_app()
    app.state.ai_service = StubAIService(configured=True, model="gemini-1.5-flash")
    client = TestClient(app)

    response = client.get("/api/v1/ai/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "AI service health retrieved successfully."
    assert payload["data"] == {
        "configured": True,
        "model": "gemini-1.5-flash",
        "status": "healthy",
    }


def test_ai_health_endpoint_unhealthy() -> None:
    app = create_app()
    app.state.ai_service = StubAIService(configured=False, model="gemini-1.5-flash")
    client = TestClient(app)

    response = client.get("/api/v1/ai/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["configured"] is False
    assert payload["data"]["status"] == "unhealthy"
