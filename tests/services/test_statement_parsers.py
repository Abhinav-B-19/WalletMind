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


def test_direction_validator_correct_debit_remains_debit() -> None:
    parser = GenericCSVParser()
    csv_data = """Date,Description,DR,CR,Balance
2026-01-01,Expense,100,,900
"""

    result = parser.parse(
        content=csv_data.encode("utf-8"),
        filename="sample.csv",
        content_type="text/csv",
    )

    assert len(result.transactions) == 1
    assert result.transactions[0].transaction_type == "debit"
    assert result.direction_corrections == 0


def test_direction_validator_correct_credit_remains_credit() -> None:
    parser = GenericCSVParser()
    csv_data = """Date,Description,DR,CR,Balance
2026-01-01,Deposit,,100,1100
"""

    result = parser.parse(
        content=csv_data.encode("utf-8"),
        filename="sample.csv",
        content_type="text/csv",
    )

    assert len(result.transactions) == 1
    assert result.transactions[0].transaction_type == "credit"
    assert result.direction_corrections == 0


def test_direction_validator_swapped_headers_get_corrected() -> None:
    parser = GenericCSVParser()
    csv_data = """Date,Description,DR,CR,Balance
2026-01-01,Opening,,1000,1000
2026-01-02,Deposit,100,,1100
2026-01-03,Expense,,50,1050
"""

    result = parser.parse(
        content=csv_data.encode("utf-8"),
        filename="sample.csv",
        content_type="text/csv",
    )

    assert len(result.transactions) == 3
    assert result.transactions[1].transaction_type == "credit"
    assert result.transactions[1].amount == Decimal("100.00")
    assert result.transactions[2].transaction_type == "debit"
    assert result.transactions[2].amount == Decimal("-50.00")
    assert result.direction_corrections == 2


def test_direction_validator_no_correction_when_balance_missing() -> None:
    parser = GenericCSVParser()
    csv_data = """Date,Description,DR,CR,Balance
2026-01-01,Expense,100,,
"""

    result = parser.parse(
        content=csv_data.encode("utf-8"),
        filename="sample.csv",
        content_type="text/csv",
    )

    assert len(result.transactions) == 1
    assert result.direction_corrections == 0


def test_direction_validator_no_correction_when_previous_balance_missing() -> None:
    parser = GenericCSVParser()
    csv_data = """Date,Description,DR,CR,Balance
2026-01-01,Deposit,100,,1100
"""

    result = parser.parse(
        content=csv_data.encode("utf-8"),
        filename="sample.csv",
        content_type="text/csv",
    )

    assert len(result.transactions) == 1
    assert result.direction_corrections == 0


def test_direction_validator_floating_point_tolerance() -> None:
    parser = GenericCSVParser()
    csv_data = """Date,Description,DR,CR,Balance
2026-01-01,Opening,,1000,1000.00
2026-01-02,Deposit,0.10,,1000.10
"""

    result = parser.parse(
        content=csv_data.encode("utf-8"),
        filename="sample.csv",
        content_type="text/csv",
    )

    assert len(result.transactions) == 2
    assert result.transactions[1].transaction_type == "credit"
    assert result.direction_corrections == 1
