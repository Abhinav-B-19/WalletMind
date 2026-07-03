from __future__ import annotations

from uuid import uuid4

from tests.api.test_statement_upload_api import _setup_client_with_statement_service
from walletmind.exceptions import AssistantNoDataError


class StubAssistantService:
    def __init__(self, result):
        self._result = result

    def chat(self, request):
        return self._result


class StubAssistantServiceNoData:
    def chat(self, request):
        raise AssistantNoDataError(
            "I couldn't find any transactions for the merchant 'amazon' "
            "in the selected statement, so I can't provide an accurate answer "
            "based only on your uploaded financial data."
        )


def test_assistant_chat_endpoint_success(tmp_path) -> None:
    client, _ = _setup_client_with_statement_service(tmp_path)

    client.app.state.financial_assistant_service = StubAssistantService(
        {
            "answer": "You spent $12.45 at Starbucks.",
            "sources": [
                {
                    "transaction_id": "tx-1",
                    "merchant": "Starbucks",
                    "date": "2026-01-05",
                    "amount": -12.45,
                }
            ],
            "confidence": 0.9,
        }
    )

    statement_id = str(uuid4())
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "statement_id": statement_id,
            "question": "How much did I spend at Starbucks?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Assistant response generated successfully."
    assert payload["data"]["answer"] == "You spent $12.45 at Starbucks."
    assert payload["data"]["sources"][0]["merchant"] == "Starbucks"


def test_assistant_chat_endpoint_no_data_returns_404(tmp_path) -> None:
    client, _ = _setup_client_with_statement_service(tmp_path)
    client.app.state.financial_assistant_service = StubAssistantServiceNoData()

    statement_id = str(uuid4())
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "statement_id": statement_id,
            "question": "How much did I spend on Amazon?",
        },
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["code"] == "ASSISTANT_NO_DATA"
    assert "merchant 'amazon'" in payload["message"]
