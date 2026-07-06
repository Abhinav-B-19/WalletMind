from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.adk.runner import WalletMindRunner


class FakeSessionService:
    def __init__(self) -> None:
        self._stored = None

    async def get_session(self, *, app_name, user_id, session_id):
        return self._stored

    async def create_session(self, **kwargs):
        self._stored = SimpleNamespace(
            app_name=kwargs["app_name"],
            user_id=kwargs["user_id"],
            id=kwargs["session_id"],
            state=kwargs.get("state", {}),
        )
        return self._stored


class FakeRunner:
    async def run_async(self, *, user_id, session_id, new_message):
        _ = (user_id, session_id, new_message)
        yield SimpleNamespace(content=SimpleNamespace(text="hello"))
        yield SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(text="world")]))


@pytest.mark.asyncio
async def test_runner_ensures_session_and_returns_structured_result():
    service = FakeSessionService()
    runner = WalletMindRunner(
        runner=FakeRunner(),
        session_service=service,
        app_name="walletmind",
    )

    result = await runner.run(
        user_id="user-1",
        session_id="session-1",
        message="ping",
    )

    assert result.user_id == "user-1"
    assert result.session_id == "session-1"
    assert result.final_response == "world"
    assert result.event_count == 2
    assert service._stored is not None
