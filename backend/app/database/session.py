"""Database engine and session factory configuration."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import DATABASE_URL, SQLITE_CONNECT_ARGS


def create_database_engine(database_url: str = DATABASE_URL) -> Engine:
    """Create a SQLAlchemy engine for the configured database.

    Args:
        database_url: SQLAlchemy database URL. Defaults to the project SQLite DB.

    Returns:
        Configured SQLAlchemy engine.
    """
    connect_args = SQLITE_CONNECT_ARGS if database_url.startswith("sqlite") else {}
    database_engine = create_engine(
        database_url,
        connect_args=connect_args,
        future=True,
    )

    if database_url.startswith("sqlite"):
        _enable_sqlite_foreign_keys(database_engine)

    return database_engine


def _enable_sqlite_foreign_keys(database_engine: Engine) -> None:
    """Enable SQLite foreign key enforcement for new connections.

    Args:
        database_engine: SQLAlchemy engine receiving the connection listener.
    """

    @event.listens_for(database_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: object, _: object) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_session_factory(bind: Engine) -> sessionmaker[Session]:
    """Create a configured SQLAlchemy session factory.

    Args:
        bind: Engine used by sessions created from the factory.

    Returns:
        SQLAlchemy session factory.
    """
    return sessionmaker(
        bind=bind,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


engine = create_database_engine()
SessionLocal = create_session_factory(engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session and close it after use.

    Yields:
        A SQLAlchemy session bound to the configured engine.
    """
    with SessionLocal() as session:
        yield session