"""Unit tests for production-grade transaction parser behavior."""

from __future__ import annotations

from decimal import Decimal

from walletmind.services.statement_parsers import GenericCSVParser


AXIS_CSV = """Name :- ABHINAV B
Currency :- INR
Statement of Account No - 922010066403616 for the period (From : 30-12-2025  To : 28-06-2026)

Tran Date,CHQNO,PARTICULARS,DR,CR,BAL,SOL
30-12-2025,-,UPI Credit,,5000.00,86481.70,014
30-12-2025,-,UPI Debit,1.00,,86480.70,014
"""


def test_axis_csv_header_detection_and_metadata_skip() -> None:
    parser = GenericCSVParser()

    result = parser.parse(
        content=AXIS_CSV.encode("utf-8"),
        filename="Axis_Statement.csv",
        content_type="text/csv",
    )

    assert result.errors == []
    assert result.metadata.get("currency") == "INR"
    assert result.metadata.get("account_number") == "922010066403616"
    assert result.transactions
    assert len(result.transactions) == 2


def test_axis_csv_normalization_debit_credit_balance_date() -> None:
    parser = GenericCSVParser()

    result = parser.parse(
        content=AXIS_CSV.encode("utf-8"),
        filename="Axis_Statement.csv",
        content_type="text/csv",
    )

    first = result.transactions[0]
    second = result.transactions[1]

    assert first.transaction_date.isoformat() == "2025-12-30"
    assert first.credit == Decimal("5000.00")
    assert first.debit is None
    assert first.amount == Decimal("5000.00")
    assert first.transaction_type == "credit"
    assert first.balance == Decimal("86481.70")

    assert second.transaction_date.isoformat() == "2025-12-30"
    assert second.debit == Decimal("-1.00")
    assert second.credit is None
    assert second.amount == Decimal("-1.00")
    assert second.transaction_type == "debit"
    assert second.balance == Decimal("86480.70")


def test_axis_csv_reference_extraction_from_chqno() -> None:
    parser = GenericCSVParser()

    result = parser.parse(
        content=AXIS_CSV.encode("utf-8"),
        filename="Axis_Statement.csv",
        content_type="text/csv",
    )

    assert result.transactions[0].reference_number == "-"


def test_csv_parse_returns_header_not_found_for_invalid_file() -> None:
    parser = GenericCSVParser()

    result = parser.parse(
        content=b"foo,bar,baz\n1,2,3\n",
        filename="invalid.csv",
        content_type="text/csv",
    )

    assert result.transactions == []
    assert "header_not_found" in result.errors
