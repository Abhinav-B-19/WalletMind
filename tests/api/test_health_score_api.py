from __future__ import annotations

from tests.api.test_statement_upload_api import (
    _create_persisted_user,
    _setup_client_with_statement_service,
)


class StubFinancialHealthService:
    def __init__(self, result):
        self._result = result

    def generate_statement_health_score(self, *, statement_uuid):
        return self._result


def test_statement_health_score_endpoint_success(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "health.csv",
                b"Date,Narration,Withdrawal,Deposit\\n2026-06-01,Salary,0,120\\n",
                "text/csv",
            )
        },
    )
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    client.app.state.financial_health_service = StubFinancialHealthService(
        {
            "overall_score": 82,
            "grade": "Good",
            "components": {
                "savings_rate": 91,
                "income_stability": 88,
                "spending_discipline": 72,
                "recurring_obligations": 80,
                "cash_flow": 79,
            },
            "strengths": ["Healthy savings behavior"],
            "weaknesses": ["Disciplined spending pattern"],
            "ai_explanation": "Your score is good due to healthy savings.",
            "recommendations": ["Reduce discretionary spending"],
        }
    )

    response = client.get(f"/api/v1/statements/{statement_uuid}/health-score")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Statement health score generated successfully."
    assert payload["data"]["overall_score"] == 82
    assert payload["data"]["grade"] == "Good"
    assert payload["data"]["components"]["savings_rate"] == 91
