from __future__ import annotations

from tests.api.test_statement_upload_api import (
    _create_persisted_user,
    _setup_client_with_statement_service,
)


class StubSpendingInsightsService:
    def __init__(self, result):
        self._result = result

    def generate_statement_insights(self, *, statement_uuid):
        return self._result

def test_statement_insights_endpoint_success(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "insights.csv",
                b"Date,Narration,Withdrawal,Deposit\\n2026-06-01,Salary,0,120\\n",
                "text/csv",
            )
        },
    )
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    fake_result = {
        "statement_uuid": statement_uuid,
        "deterministic_summary": {
            "statement_uuid": statement_uuid,
            "transaction_count": 1,
            "credit_count": 1,
            "debit_count": 0,
            "cash_flow": {
                "total_income": 120.0,
                "total_expenses": 0.0,
                "net_cash_flow": 120.0,
                "savings_rate": 100.0,
            },
            "category_breakdown": {},
            "top_spending_categories": [],
            "top_merchants": [],
            "largest_expense": None,
            "largest_income": None,
            "monthly_averages": {"income": 120.0, "expenses": 0.0, "net": 120.0},
            "monthly_trend": [],
            "recurring_subscriptions": [],
        },
        "insights": {
            "summary": "Good month",
            "strengths": ["Positive cash flow"],
            "concerns": [],
            "recommendations": [
                {
                    "title": "Keep emergency fund",
                    "description": "Set aside part of income",
                    "priority": "low",
                }
            ],
        },
        "model": "gemini-1.5-flash",
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "finish_reason": "stop",
    }

    client.app.state.spending_insights_service = StubSpendingInsightsService(
        fake_result
    )

    response = client.get(f"/api/v1/statements/{statement_uuid}/insights")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["insights"]["summary"] == "Good month"
    assert payload["data"]["total_tokens"] == 30
