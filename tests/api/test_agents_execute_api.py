from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

from tests.api.test_statement_upload_api import _setup_client_with_statement_service


class StubCoordinatorAgent:
    def __init__(self) -> None:
        self.last_context = None

    async def execute(self, *, context):
        self.last_context = context
        return SimpleNamespace(
            result={
                "overall_status": "COMPLETED",
                "decision_record": {
                    "intent": "analyze_finances",
                    "capabilities": ["financial_health", "insights"],
                    "selected_agents": ["health_agent", "insights_agent"],
                    "reason": (
                        "Complex intent detected; selected multi-agent execution "
                        "plan."
                    ),
                    "execution_mode": "multi",
                    "execution_timestamp": "2026-01-01T00:00:00Z",
                },
                "execution_trace": [],
                "individual_agent_results": [],
                "metadata": {
                    "selected_agent_count": 2,
                    "resolved_statement_uuid": context.extras["inputs"].get(
                        "statement_uuid"
                    ),
                },
            }
        )


class StubStatementUploadService:
    def __init__(self, statements):
        self._statements = statements

    def list_statements(self, user_uuid):
        _ = user_uuid
        return self._statements


def test_agents_execute_endpoint_success(tmp_path) -> None:
    client, _ = _setup_client_with_statement_service(tmp_path)
    client.app.state.coordinator_agent = StubCoordinatorAgent()
    client.app.state.statement_upload_service = StubStatementUploadService(
        statements=[]
    )

    response = client.post(
        "/api/v1/agents/execute",
        json={
            "query": "Analyze my finances",
            "user_id": "user-1",
            "session_id": "session-1",
            "inputs": {
                "statement_uuid": "11111111-1111-1111-1111-111111111111",
                "statement_id": "11111111-1111-1111-1111-111111111111",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Coordinator execution completed successfully."
    assert payload["data"]["overall_status"] == "COMPLETED"
    assert payload["data"]["decision_record"]["execution_mode"] == "multi"


def test_agents_execute_endpoint_validation_error(tmp_path) -> None:
    client, _ = _setup_client_with_statement_service(tmp_path)
    client.app.state.coordinator_agent = StubCoordinatorAgent()
    client.app.state.statement_upload_service = StubStatementUploadService(
        statements=[]
    )

    response = client.post(
        "/api/v1/agents/execute",
        json={
            "query": "",
            "user_id": "user-1",
            "session_id": "session-1",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["code"] == "VALIDATION_ERROR"


def test_agents_execute_auto_resolves_single_processed_statement(tmp_path) -> None:
    client, _ = _setup_client_with_statement_service(tmp_path)
    coordinator = StubCoordinatorAgent()
    client.app.state.coordinator_agent = coordinator
    client.app.state.statement_upload_service = StubStatementUploadService(
        statements=[
            {
                "statement_uuid": "11111111-1111-1111-1111-111111111111",
                "status": "ready_for_analysis",
                "original_filename": "latest.csv",
                "uploaded_at": "2026-01-01T00:00:00Z",
            }
        ]
    )

    response = client.post(
        "/api/v1/agents/execute",
        json={
            "query": "Analyze my finances",
            "user_id": "user-1",
            "session_id": "session-1",
            "user_uuid": str(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
            "inputs": {},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert (
        payload["data"]["metadata"]["resolved_statement_uuid"]
        == "11111111-1111-1111-1111-111111111111"
    )
    assert coordinator.last_context is not None
    assert (
        coordinator.last_context.extras["inputs"]["statement_id"]
        == "11111111-1111-1111-1111-111111111111"
    )


def test_agents_execute_returns_selection_required_for_multiple_candidates(
    tmp_path,
) -> None:
    client, _ = _setup_client_with_statement_service(tmp_path)
    client.app.state.coordinator_agent = StubCoordinatorAgent()
    client.app.state.statement_upload_service = StubStatementUploadService(
        statements=[
            {
                "statement_uuid": "11111111-1111-1111-1111-111111111111",
                "status": "ready_for_analysis",
                "original_filename": "a.csv",
                "uploaded_at": "2026-01-01T00:00:00Z",
            },
            {
                "statement_uuid": "22222222-2222-2222-2222-222222222222",
                "status": "completed",
                "original_filename": "b.csv",
                "uploaded_at": "2026-01-02T00:00:00Z",
            },
        ]
    )

    response = client.post(
        "/api/v1/agents/execute",
        json={
            "query": "Analyze my finances",
            "user_id": "user-1",
            "session_id": "session-1",
            "user_uuid": str(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
            "inputs": {},
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["code"] == "MULTIPLE_PROCESSED_STATEMENTS"
    assert len(payload["details"]["candidates"]) == 2
