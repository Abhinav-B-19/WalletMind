"""Transaction persistence and query service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import json
from sqlalchemy import or_
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.statement import Statement
from backend.app.models.transaction import Transaction
from walletmind.exceptions import StatementNotFoundError, StatementStorageError
from walletmind.schemas.transaction import TransactionCreateDTO, TransactionDTO
from walletmind.services.transaction_normalizer import TransactionNormalizer


class TransactionService:
    """Persists normalized transactions and handles duplicate prevention and querying."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._normalizer = TransactionNormalizer()

    def store_transactions(
        self,
        *,
        statement_uuid: UUID | str,
        transactions: list[TransactionCreateDTO],
    ) -> tuple[int, int]:
        parsed_uuid = self._coerce_uuid(statement_uuid)

        with self._session_factory() as session:
            statement = session.scalar(select(Statement).where(Statement.uuid == str(parsed_uuid)))
            if statement is None:
                raise StatementNotFoundError(f"Statement '{parsed_uuid}' was not found")

            inserted = 0
            duplicates = 0
            seen_signatures: set[tuple[date, str, Decimal]] = set()
            for tx in transactions:
                enriched = self._normalizer.enrich(
                    transaction=tx,
                    account_holder_name=statement.user.full_name if statement.user else None,
                )

                signature = (tx.transaction_date, tx.description, tx.amount)
                if signature in seen_signatures:
                    duplicates += 1
                    continue

                exists = session.scalar(
                    select(Transaction.id).where(
                        Transaction.statement_id == statement.id,
                        Transaction.transaction_date == tx.transaction_date,
                        Transaction.description == tx.description,
                        Transaction.amount == tx.amount,
                    )
                )
                if exists:
                    duplicates += 1
                    continue

                record = Transaction(
                    statement_id=statement.id,
                    transaction_date=tx.transaction_date,
                    description=tx.description,
                    debit=tx.debit,
                    credit=tx.credit,
                    amount=tx.amount,
                    transaction_type=tx.transaction_type,
                    balance=tx.balance,
                    currency=tx.currency,
                    reference_number=tx.reference_number,
                    merchant_name=enriched.merchant_name,
                    bank_gateway=enriched.bank_gateway,
                    category=enriched.category,
                    raw_description=enriched.raw_description,
                    clean_description=enriched.clean_description,
                    normalized_transaction_type=enriched.normalized_transaction_type,
                    is_internal_transfer=enriched.is_internal_transfer,
                    is_income=enriched.is_income,
                    is_expense=enriched.is_expense,
                    raw_row_json=json.dumps(tx.raw_row_json, ensure_ascii=True, sort_keys=True),
                )
                session.add(record)
                seen_signatures.add(signature)
                inserted += 1

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise StatementStorageError("Failed to persist parsed transactions") from exc

            return inserted, duplicates

    def get_statement_transactions(self, *, statement_uuid: UUID | str) -> list[TransactionDTO]:
        parsed_uuid = self._coerce_uuid(statement_uuid)
        with self._session_factory() as session:
            statement = session.scalar(select(Statement).where(Statement.uuid == str(parsed_uuid)))
            if statement is None:
                raise StatementNotFoundError(f"Statement '{parsed_uuid}' was not found")

            rows = session.scalars(
                select(Transaction)
                .where(Transaction.statement_id == statement.id)
                .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            ).all()

            return [self._to_dto(row, statement.uuid) for row in rows]

    def list_transactions(
        self,
        *,
        statement_uuid: UUID | str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        q: str | None = None,
        normalized_type: str | None = None,
        category: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[TransactionDTO]:
        offset = max(page - 1, 0) * page_size

        with self._session_factory() as session:
            query = (
                select(Transaction, Statement.uuid)
                .join(Statement, Statement.id == Transaction.statement_id)
                .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            )

            filters = []
            if statement_uuid is not None:
                parsed_uuid = self._coerce_uuid(statement_uuid)
                filters.append(Statement.uuid == str(parsed_uuid))
            if from_date is not None:
                filters.append(Transaction.transaction_date >= from_date)
            if to_date is not None:
                filters.append(Transaction.transaction_date <= to_date)
            if min_amount is not None:
                filters.append(Transaction.amount >= min_amount)
            if max_amount is not None:
                filters.append(Transaction.amount <= max_amount)
            if normalized_type is not None:
                filters.append(Transaction.normalized_transaction_type == normalized_type)
            if category is not None:
                filters.append(Transaction.category == category)

            if q:
                pattern = f"%{q.strip()}%"
                filters.append(
                    or_(
                        Transaction.merchant_name.ilike(pattern),
                        Transaction.category.ilike(pattern),
                        Transaction.clean_description.ilike(pattern),
                    )
                )

            if filters:
                query = query.where(and_(*filters))

            rows = session.execute(query.offset(offset).limit(page_size)).all()
            return [self._to_dto(record, statement_uuid_value) for record, statement_uuid_value in rows]

    @staticmethod
    def _coerce_uuid(value: UUID | str) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _to_dto(record: Transaction, statement_uuid: str) -> TransactionDTO:
        return TransactionDTO(
            transaction_uuid=UUID(record.uuid),
            statement_uuid=UUID(statement_uuid),
            transaction_date=record.transaction_date,
            description=record.description,
            debit=record.debit,
            credit=record.credit,
            amount=record.amount,
            transaction_type=record.transaction_type,
            balance=record.balance,
            currency=record.currency,
            reference_number=record.reference_number,
            merchant_name=record.merchant_name,
            bank_gateway=record.bank_gateway,
            category=record.category,
            raw_description=record.raw_description,
            clean_description=record.clean_description,
            normalized_transaction_type=record.normalized_transaction_type,
            flags={
                "is_internal_transfer": bool(record.is_internal_transfer),
                "is_income": bool(record.is_income),
                "is_expense": bool(record.is_expense),
            },
            raw_row_json=json.loads(record.raw_row_json),
            created_at=record.created_at,
        )
