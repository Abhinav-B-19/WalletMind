from __future__ import annotations

from tests.api.test_statement_upload_api import (
    _create_persisted_user,
    _setup_client_with_statement_service,
)


class StubBudgetService:
    def __init__(self, result):
        self._result = result

    def generate_statement_budget_recommendations(self, *, statement_uuid):
        return self._result


def test_statement_budget_recommendations_endpoint_success(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "budget.csv",
                b"Date,Narration,Withdrawal,Deposit\\n2026-06-01,Salary,0,120\\n",
                "text/csv",
            )
        },
    )
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    client.app.state.budget_service = StubBudgetService(
        {
            "monthly_budget": {
                "Food": {
                    "historical": 8500.0,
                    "recommended": 7500.0,
                    "potential_saving": 1000.0,
                }
            },
            "overall_potential_savings": 4500.0,
            "priority_recommendations": [
                {
                    "title": (
                        "Reduce Food spending by 1000.00 per month "
                        "to improve savings capacity."
                    ),
                    "priority": "high",
                    "category": "Food",
                    "estimated_monthly_saving": 1000.0,
                }
            ],
            "ai_summary": (
                "Your budget plan prioritizes high-impact " "overspending categories."
            ),
            "ai_recommendations": [
                "Set weekly caps for food and shopping.",
                "Move savings transfer to salary day.",
            ],
        }
    )

    response = client.get(f"/api/v1/statements/{statement_uuid}/budget-recommendations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert (
        payload["message"] == "Statement budget recommendations generated successfully."
    )
    assert payload["data"]["overall_potential_savings"] == 4500.0
    assert payload["data"]["monthly_budget"]["Food"]["recommended"] == 7500.0
