from __future__ import annotations

from tests.api.test_statement_upload_api import (
    _create_persisted_user,
    _setup_client_with_statement_service,
)


class StubFinancialReportService:
    def __init__(self, result):
        self._result = result

    def generate_monthly_report(self, *, statement_uuid):
        return self._result


def test_statement_monthly_report_endpoint_success(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "report.csv",
                b"Date,Narration,Withdrawal,Deposit\\n2026-06-01,Salary,0,120\\n",
                "text/csv",
            )
        },
    )
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    client.app.state.financial_report_service = StubFinancialReportService(
        {
            "executive_summary": "Stable month with practical savings opportunities.",
            "financial_health": {"overall_score": 78, "grade": "Good"},
            "income_summary": {"total_income": 120.0},
            "expense_summary": {"total_expenses": 0.0},
            "cash_flow": {"net_cash_flow": 120.0},
            "spending_insights": {"top_spending_categories": []},
            "budget_recommendations": {"overall_potential_savings": 40.0},
            "health_score": {"overall_score": 78, "grade": "Good"},
            "strengths": ["Positive cash flow"],
            "risks": ["Limited data window"],
            "action_plan": [
                "Track weekly expenses",
                "Preserve emergency buffer",
                "Review discretionary spending",
            ],
        }
    )

    response = client.get(f"/api/v1/statements/{statement_uuid}/monthly-report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Statement monthly report generated successfully."
    assert payload["data"]["health_score"]["overall_score"] == 78
    assert len(payload["data"]["action_plan"]) == 3
