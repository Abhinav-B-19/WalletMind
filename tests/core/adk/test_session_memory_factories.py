from __future__ import annotations

from backend.app.adk.memory import WalletMindMemoryServiceFactory
from backend.app.adk.session import WalletMindSessionServiceFactory


class FakeSessionService:
    pass


class FakeMemoryService:
    pass


def test_session_factory_creates_in_memory_service(monkeypatch):
    monkeypatch.setattr(
        WalletMindSessionServiceFactory,
        "_load_in_memory_session_service",
        staticmethod(lambda: FakeSessionService),
    )

    service = WalletMindSessionServiceFactory().create()

    assert isinstance(service, FakeSessionService)


def test_memory_factory_creates_in_memory_service(monkeypatch):
    monkeypatch.setattr(
        WalletMindMemoryServiceFactory,
        "_load_in_memory_memory_service",
        staticmethod(lambda: FakeMemoryService),
    )

    service = WalletMindMemoryServiceFactory().create()

    assert isinstance(service, FakeMemoryService)
