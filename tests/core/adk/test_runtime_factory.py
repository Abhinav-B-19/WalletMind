from __future__ import annotations

from backend.app.adk.config import AdkRuntimeSettings
from backend.app.adk.memory import WalletMindMemoryServiceFactory
from backend.app.adk.runtime import WalletMindAdkRuntimeFactory
from backend.app.adk.session import WalletMindSessionServiceFactory
from backend.app.adk.workflow import WalletMindWorkflowFactory


class FakeSessionService:
    pass


class FakeMemoryService:
    pass


class FakeWorkflow:
    name = "walletmind_root_workflow"


class FakeRawRunner:
    def __init__(self, *, agent, app_name, session_service, memory_service):
        self.agent = agent
        self.app_name = app_name
        self.session_service = session_service
        self.memory_service = memory_service


def test_runtime_factory_initializes_all_components(monkeypatch):
    monkeypatch.setattr(
        WalletMindSessionServiceFactory,
        "create",
        lambda self: FakeSessionService(),
    )
    monkeypatch.setattr(
        WalletMindMemoryServiceFactory,
        "create",
        lambda self: FakeMemoryService(),
    )
    monkeypatch.setattr(
        WalletMindWorkflowFactory,
        "create",
        lambda self: FakeWorkflow(),
    )
    monkeypatch.setattr(
        WalletMindAdkRuntimeFactory,
        "_load_runner_class",
        staticmethod(lambda: FakeRawRunner),
    )

    settings = AdkRuntimeSettings(
        app_name="walletmind",
        root_workflow_name="walletmind_root_workflow",
        default_user_id="walletmind-system",
        default_session_prefix="wm-session",
        model_name="gemini-2.5-flash",
    )

    runtime = WalletMindAdkRuntimeFactory(settings=settings).create()

    assert runtime.settings.app_name == "walletmind"
    assert isinstance(runtime.session_service, FakeSessionService)
    assert isinstance(runtime.memory_service, FakeMemoryService)
    assert isinstance(runtime.root_workflow, FakeWorkflow)

    raw = runtime.runner.raw_runner
    assert isinstance(raw, FakeRawRunner)
    assert raw.app_name == "walletmind"
    assert raw.agent is runtime.root_workflow
    assert raw.session_service is runtime.session_service
    assert raw.memory_service is runtime.memory_service
