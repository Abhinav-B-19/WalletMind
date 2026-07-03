"""Database initialization helpers for WalletMind."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from backend.app.core.config import DATABASE_DIR
from backend.app.database.base import Base
from backend.app.database.session import engine
from backend.app.models.statement import Statement  # noqa: F401
from backend.app.models.transaction import Transaction  # noqa: F401
from backend.app.models.user import User  # noqa: F401


def init_database(database_engine: Engine = engine) -> None:
    """Create the database directory and all registered tables.

    Args:
        database_engine: Engine used for schema creation.
    """
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=database_engine)
    _reconcile_sqlite_statement_schema(database_engine)
    _reconcile_sqlite_transaction_schema(database_engine)


def _reconcile_sqlite_statement_schema(database_engine: Engine) -> None:
    """Add newly introduced nullable statement columns when table already exists.

    SQLite `create_all` does not alter existing tables, so we patch drifted dev
    databases by adding missing columns in-place without deleting data.
    """

    if database_engine.dialect.name != "sqlite":
        return

    inspector = inspect(database_engine)
    if "statements" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("statements")
    }
    missing_columns = {
        "detected_file_type": "VARCHAR(32)",
        "parser_type": "VARCHAR(32)",
        "classification_confidence": "FLOAT",
        "classification_method": "VARCHAR(120)",
        "classified_at": "DATETIME",
        "parsed_transaction_count": "INTEGER DEFAULT 0",
        "failed_transaction_count": "INTEGER DEFAULT 0",
        "parsed_at": "DATETIME",
        "rows_read": "INTEGER DEFAULT 0",
        "rows_parsed": "INTEGER DEFAULT 0",
        "rows_skipped": "INTEGER DEFAULT 0",
        "direction_corrections": "INTEGER DEFAULT 0",
        "parsing_duration_ms": "INTEGER DEFAULT 0",
        "processing_started_at": "DATETIME",
        "processing_completed_at": "DATETIME",
        "processing_error": "VARCHAR(500)",
    }

    statements = []
    for column_name, column_type in missing_columns.items():
        if column_name not in existing_columns:
            statements.append(
                text(
                    f"ALTER TABLE statements ADD COLUMN {column_name} {column_type}"  # noqa: S608
                )
            )

    if not statements:
        return

    with database_engine.begin() as connection:
        for statement in statements:
            connection.execute(statement)


def _reconcile_sqlite_transaction_schema(database_engine: Engine) -> None:
    """Add newly introduced transaction enrichment columns for SQLite dev DBs."""

    if database_engine.dialect.name != "sqlite":
        return

    inspector = inspect(database_engine)
    if "transactions" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("transactions")
    }
    missing_columns = {
        "merchant_name": "VARCHAR(160)",
        "bank_gateway": "VARCHAR(160)",
        "category": "VARCHAR(64) DEFAULT 'Others'",
        "subcategory": "VARCHAR(64)",
        "payment_channel": "VARCHAR(64) DEFAULT 'Bank Transfer'",
        "transaction_kind": "VARCHAR(32) DEFAULT 'other'",
        "confidence_score": "INTEGER DEFAULT 0",
        "is_transfer": "BOOLEAN DEFAULT 0",
        "raw_description": "VARCHAR(255) DEFAULT ''",
        "clean_description": "VARCHAR(255) DEFAULT ''",
        "normalized_transaction_type": "VARCHAR(32) DEFAULT 'other'",
        "is_internal_transfer": "BOOLEAN DEFAULT 0",
        "is_subscription": "BOOLEAN DEFAULT 0",
        "is_recurring": "BOOLEAN DEFAULT 0",
        "is_salary": "BOOLEAN DEFAULT 0",
        "is_cash": "BOOLEAN DEFAULT 0",
        "is_atm": "BOOLEAN DEFAULT 0",
        "is_loan": "BOOLEAN DEFAULT 0",
        "is_investment": "BOOLEAN DEFAULT 0",
        "is_tax": "BOOLEAN DEFAULT 0",
        "is_income": "BOOLEAN DEFAULT 0",
        "is_expense": "BOOLEAN DEFAULT 0",
    }

    statements = []
    for column_name, column_type in missing_columns.items():
        if column_name not in existing_columns:
            statements.append(
                text(
                    f"ALTER TABLE transactions ADD COLUMN {column_name} {column_type}"  # noqa: S608
                )
            )

    if not statements:
        return

    with database_engine.begin() as connection:
        for statement in statements:
            connection.execute(statement)

        # Backfill safe defaults for existing rows after column additions.
        connection.execute(
            text(
                "UPDATE transactions SET payment_channel = COALESCE(payment_channel, 'Bank Transfer')"
            )
        )
        connection.execute(
            text("UPDATE transactions SET transaction_kind = COALESCE(transaction_kind, 'other')")
        )
        connection.execute(
            text("UPDATE transactions SET confidence_score = COALESCE(confidence_score, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_transfer = COALESCE(is_transfer, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_internal_transfer = COALESCE(is_internal_transfer, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_subscription = COALESCE(is_subscription, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_recurring = COALESCE(is_recurring, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_salary = COALESCE(is_salary, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_cash = COALESCE(is_cash, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_atm = COALESCE(is_atm, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_loan = COALESCE(is_loan, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_investment = COALESCE(is_investment, 0)")
        )
        connection.execute(
            text("UPDATE transactions SET is_tax = COALESCE(is_tax, 0)")
        )


if __name__ == "__main__":
    init_database()