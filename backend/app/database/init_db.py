"""Database initialization helpers for WalletMind."""

from sqlalchemy.engine import Engine

from backend.app.core.config import DATABASE_DIR
from backend.app.database.base import Base
from backend.app.database.session import engine
from backend.app.models.user import User  # noqa: F401


def init_database(database_engine: Engine = engine) -> None:
    """Create the database directory and all registered tables.

    Args:
        database_engine: Engine used for schema creation.
    """
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=database_engine)


if __name__ == "__main__":
    init_database()