"""Database package exports."""

from backend.app.database.base import Base
from backend.app.database.session import SessionLocal, create_database_engine, engine, get_session


def init_database(*args, **kwargs):
    """Lazily import init_db to avoid package-level model registration side effects."""

    from backend.app.database.init_db import init_database as _init_database

    return _init_database(*args, **kwargs)

__all__ = [
    "Base",
    "SessionLocal",
    "create_database_engine",
    "engine",
    "get_session",
    "init_database",
]