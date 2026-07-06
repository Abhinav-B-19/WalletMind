from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from backend.app.agents.base_agent import WalletMindBaseAgent
from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.types import AgentExecutionStatus, AgentMetadata


class FakeAdkAgent:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@dataclass
class HookState:
    before_called: bool = False
    after_called: bool = False


class ExampleAgent(WalletMindBaseAgent):
    def __init__(self, *, hook_state: HookState | None = None):
        super().__init__(
            metadata=AgentMetadata(
                name="example_agent",
                description="Example agent for runtime tests.",
                version="1.0.0",
                tags=("test",),
            )
        )
        self._hook_state = hook_state or HookState()

    def build_adk_agent_kwargs(self) -> dict[str, object]:
        return {"instruction": "infrastructure-only"}

    async def before_execute(self, *, context: AgentExecutionContext) -> None:
        _ = context
        self._hook_state.before_called = True

    async def after_execute(
        self,
        *,
        context: AgentExecutionContext,
        result,
    ) -> None:
        _ = (context, result)
        self._hook_state.after_called = True

    async def execute_impl(self, *, context: AgentExecutionContext) -> object:
        _ = context
        return {"final_response": "ok", "event_count": 2}


def test_base_agent_execute_returns_standardized_result(monkeypatch):
    monkeypatch.setattr(
        WalletMindBaseAgent,
        "_load_adk_agent_class",
        staticmethod(lambda: FakeAdkAgent),
    )

    hook_state = HookState()
    agent = ExampleAgent(hook_state=hook_state)

    result = asyncio.run(
        agent.execute(
            context=AgentExecutionContext(
                user_id="user-1",
                session_id="session-1",
                message="hello",
            )
        )
    )

    assert result.agent_name == "example_agent"
    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.result == {"final_response": "ok", "event_count": 2}
    assert result.errors == []
    assert len(result.trace) == 1
    assert result.trace[0].status == AgentExecutionStatus.COMPLETED
    assert hook_state.before_called is True
    assert hook_state.after_called is True


def test_base_agent_adk_agent_is_composed_and_memoized(monkeypatch):
    monkeypatch.setattr(
        WalletMindBaseAgent,
        "_load_adk_agent_class",
        staticmethod(lambda: FakeAdkAgent),
    )
    agent = ExampleAgent()

    first = agent.adk_agent
    second = agent.adk_agent

    assert first is second
    assert first.kwargs["name"] == "example_agent"
    assert first.kwargs["description"] == "Example agent for runtime tests."
    assert first.kwargs["instruction"] == "infrastructure-only"


def test_base_agent_rejects_empty_message(monkeypatch):
    monkeypatch.setattr(
        WalletMindBaseAgent,
        "_load_adk_agent_class",
        staticmethod(lambda: FakeAdkAgent),
    )
    agent = ExampleAgent()

    with pytest.raises(ValueError, match="must not be empty"):
        asyncio.run(
            agent.execute(
                context=AgentExecutionContext(
                    user_id="user-1",
                    session_id="session-1",
                    message="   ",
                )
            )
        )
