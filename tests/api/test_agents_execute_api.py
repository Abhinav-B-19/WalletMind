from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import UUID

from backend.app.agents.coordinator_agent import CoordinatorAgent
from tests.api.test_statement_upload_api import (
    _create_persisted_user,
    _setup_client_with_statement_service,
)


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


def test_agents_execute_preserves_assistant_payload_through_pipeline(
    tmp_path,
    monkeypatch,
) -> None:
    client, _ = _setup_client_with_statement_service(tmp_path)

    stage_payloads: dict[str, dict[str, Any]] = {}
    agent_execute_payloads: dict[str, dict[str, Any]] = {}

    registry = client.app.state.agent_registry
    coordinator = client.app.state.coordinator_agent

    async def _fake_run_async(*, args: dict[str, Any], tool_context: Any = None) -> dict[str, Any]:
        _ = tool_context
        return {"ok": True, "args": args}

    for agent_name in (
        "health_agent",
        "insights_agent",
        "budget_agent",
        "report_agent",
        "assistant_agent",
    ):
        agent = registry.discover_by_name(agent_name)
        assert agent is not None
        monkeypatch.setattr(agent._tool, "run_async", _fake_run_async)

        original_execute = agent.execute

        async def _wrapped_execute(*, context, _name: str = agent_name, _original=original_execute):
            agent_execute_payloads[_name] = dict(context.extras or {})
            return await _original(context=context)

        monkeypatch.setattr(agent, "execute", _wrapped_execute)

    original_build_payload = CoordinatorAgent._build_agent_payload

    def _wrapped_build_payload(*, request, target_agent_name):
        payload = original_build_payload(
            request=request,
            target_agent_name=target_agent_name,
        )
        if target_agent_name == "assistant_agent":
            stage_payloads["stage1"] = dict(payload)
        return payload

    monkeypatch.setattr(
        CoordinatorAgent,
        "_build_agent_payload",
        staticmethod(_wrapped_build_payload),
    )

    original_build_context = CoordinatorAgent._build_agent_context

    def _wrapped_build_context(*, base_context, request, target_agent_name):
        assistant_context = original_build_context(
            base_context=base_context,
            request=request,
            target_agent_name=target_agent_name,
        )
        if target_agent_name == "assistant_agent":
            stage_payloads["stage2"] = dict(assistant_context.extras or {})
        return assistant_context

    monkeypatch.setattr(
        CoordinatorAgent,
        "_build_agent_context",
        staticmethod(_wrapped_build_context),
    )

    assistant = registry.discover_by_name("assistant_agent")
    assert assistant is not None

    original_validate = assistant.validate

    def _wrapped_validate(*, context):
        stage_payloads["stage4"] = dict(context.extras or {})
        return original_validate(context=context)

    monkeypatch.setattr(assistant, "validate", _wrapped_validate)

    original_execute_impl = assistant.execute_impl

    async def _wrapped_execute_impl(*, context):
        stage_payloads["stage5"] = dict(context.extras or {})
        return await original_execute_impl(context=context)

    monkeypatch.setattr(assistant, "execute_impl", _wrapped_execute_impl)

    client.app.state.statement_upload_service = StubStatementUploadService(statements=[])

    response = client.post(
        "/api/v1/agents/execute",
        json={
            "query": "Analyze my finances",
            "user_id": "judge-demo-user",
            "session_id": "judge-demo-session",
            "user_uuid": str(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
            "inputs": {
                "statement_uuid": "11111111-1111-1111-1111-111111111111",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True

    result = payload["data"]
    assert result["overall_status"] == "COMPLETED"
    assert result["metadata"]["selected_agent_count"] == 5
    assert result["metadata"]["successful_agent_count"] == 5
    assert result["metadata"]["failed_agent_count"] == 0

    expected_assistant_payload = {
        "statement_id": "11111111-1111-1111-1111-111111111111",
        "question": "Analyze my finances",
    }

    assert stage_payloads["stage1"] == expected_assistant_payload
    assert stage_payloads["stage2"] == expected_assistant_payload
    assert agent_execute_payloads["assistant_agent"] == expected_assistant_payload
    assert stage_payloads["stage4"] == expected_assistant_payload
    assert stage_payloads["stage5"] == expected_assistant_payload

    expected_uuid_payload = {"statement_uuid": "11111111-1111-1111-1111-111111111111"}
    assert agent_execute_payloads["health_agent"] == expected_uuid_payload
    assert agent_execute_payloads["insights_agent"] == expected_uuid_payload
    assert agent_execute_payloads["budget_agent"] == expected_uuid_payload
    assert agent_execute_payloads["report_agent"] == expected_uuid_payload

    statuses = {step["agent_name"]: step["status"] for step in result["execution_trace"]}
    assert statuses["health_agent"] == "COMPLETED"
    assert statuses["insights_agent"] == "COMPLETED"
    assert statuses["budget_agent"] == "COMPLETED"
    assert statuses["report_agent"] == "COMPLETED"
    assert statuses["assistant_agent"] == "COMPLETED"


def test_agents_execute_live_api_with_real_processed_statement_payload_propagation(
    tmp_path,
    monkeypatch,
) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "runtime.csv",
                (
                    b"Date,Narration,Withdrawal,Deposit\n"
                    b"2026-06-01,Salary,0,1200\n"
                    b"2026-06-02,Groceries,120,0\n"
                ),
                "text/csv",
            )
        },
    )
    assert upload.status_code == 201
    statement_uuid = upload.json()["data"]["statement_uuid"]

    stage_payloads: dict[str, dict[str, Any]] = {}
    execute_payloads: dict[str, dict[str, Any]] = {}

    registry = client.app.state.agent_registry

    async def _fake_run_async(*, args: dict[str, Any], tool_context: Any = None) -> dict[str, Any]:
        _ = tool_context
        return {"ok": True, "args": args}

    for agent_name in (
        "health_agent",
        "insights_agent",
        "budget_agent",
        "report_agent",
        "assistant_agent",
    ):
        agent = registry.discover_by_name(agent_name)
        assert agent is not None
        monkeypatch.setattr(agent._tool, "run_async", _fake_run_async)
        original_execute = agent.execute

        async def _wrapped_execute(*, context, _name: str = agent_name, _original=original_execute):
            execute_payloads[_name] = dict(context.extras or {})
            return await _original(context=context)

        monkeypatch.setattr(agent, "execute", _wrapped_execute)

    original_build_context = CoordinatorAgent._build_agent_context

    def _wrapped_build_context(*, base_context, request, target_agent_name):
        built = original_build_context(
            base_context=base_context,
            request=request,
            target_agent_name=target_agent_name,
        )
        if target_agent_name == "assistant_agent":
            stage_payloads["assistant_stage2"] = dict(built.extras or {})
        if target_agent_name == "health_agent":
            stage_payloads["health_stage2"] = dict(built.extras or {})
        return built

    monkeypatch.setattr(
        CoordinatorAgent,
        "_build_agent_context",
        staticmethod(_wrapped_build_context),
    )

    assistant = registry.discover_by_name("assistant_agent")
    assert assistant is not None

    original_validate = assistant.validate

    def _wrapped_validate(*, context):
        stage_payloads["assistant_stage4"] = dict(context.extras or {})
        return original_validate(context=context)

    monkeypatch.setattr(assistant, "validate", _wrapped_validate)

    original_execute_impl = assistant.execute_impl

    async def _wrapped_execute_impl(*, context):
        stage_payloads["assistant_stage5"] = dict(context.extras or {})
        return await original_execute_impl(context=context)

    monkeypatch.setattr(assistant, "execute_impl", _wrapped_execute_impl)

    response = client.post(
        "/api/v1/agents/execute",
        json={
            "query": "Analyze my finances",
            "user_id": "judge-demo-user",
            "session_id": "judge-demo-session",
            "user_uuid": user.uuid,
            "inputs": {
                "statement_uuid": statement_uuid,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    result = body["data"]

    assert result["overall_status"] == "COMPLETED"
    assert result["metadata"]["selected_agent_count"] == 5
    assert result["metadata"]["successful_agent_count"] == 5
    assert result["metadata"]["failed_agent_count"] == 0

    expected_assistant_payload = {
        "statement_id": statement_uuid,
        "question": "Analyze my finances",
    }
    expected_health_payload = {"statement_uuid": statement_uuid}

    assert stage_payloads["assistant_stage2"] == expected_assistant_payload
    assert execute_payloads["assistant_agent"] == expected_assistant_payload
    assert stage_payloads["assistant_stage4"] == expected_assistant_payload
    assert stage_payloads["assistant_stage5"] == expected_assistant_payload

    assert stage_payloads["health_stage2"] == expected_health_payload
    assert execute_payloads["health_agent"] == expected_health_payload

    statuses = {step["agent_name"]: step["status"] for step in result["execution_trace"]}
    assert statuses["health_agent"] == "COMPLETED"
    assert statuses["insights_agent"] == "COMPLETED"
    assert statuses["budget_agent"] == "COMPLETED"
    assert statuses["report_agent"] == "COMPLETED"
    assert statuses["assistant_agent"] == "COMPLETED"
