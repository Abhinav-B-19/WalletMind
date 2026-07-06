from __future__ import annotations

from backend.app.adk.config import AdkRuntimeSettings
from backend.app.adk.workflow import WalletMindWorkflowFactory


class FakeWorkflow:
    def __init__(self, *, name, edges):
        self.name = name
        self.edges = edges


def fake_node_decorator(*, name=None):
    def decorator(fn):
        fn._node_name = name
        return fn

    return decorator


def test_workflow_factory_creates_bootstrap_workflow(monkeypatch):
    monkeypatch.setattr(
        WalletMindWorkflowFactory,
        "_load_workflow_class",
        staticmethod(lambda: FakeWorkflow),
    )
    monkeypatch.setattr(
        WalletMindWorkflowFactory,
        "_load_node_decorator",
        staticmethod(lambda: fake_node_decorator),
    )

    settings = AdkRuntimeSettings(
        app_name="walletmind",
        root_workflow_name="walletmind_root_workflow",
        default_user_id="walletmind-system",
        default_session_prefix="wm-session",
        model_name="gemini-2.5-flash",
    )
    workflow = WalletMindWorkflowFactory(settings=settings).create()

    assert workflow.name == "walletmind_root_workflow"
    assert len(workflow.edges) == 1
    start, bootstrap = workflow.edges[0]
    assert start == "START"
    assert callable(bootstrap)
    assert getattr(bootstrap, "_node_name") == "walletmind_bootstrap"
