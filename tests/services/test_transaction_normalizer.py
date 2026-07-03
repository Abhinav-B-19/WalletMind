"""Unit tests for deterministic transaction enrichment rules."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from walletmind.schemas.transaction import TransactionCreateDTO
from walletmind.services.transaction_normalizer import TransactionNormalizer


def _tx(*, description: str, amount: Decimal, tx_type: str) -> TransactionCreateDTO:
    return TransactionCreateDTO(
        transaction_date=date(2026, 7, 3),
        description=description,
        debit=amount if tx_type == "debit" else None,
        credit=amount if tx_type == "credit" else None,
        amount=amount,
        transaction_type=tx_type,
        balance=Decimal("1000.00"),
        currency="INR",
        reference_number="-",
        raw_row_json={"row": 1},
    )


def test_merchant_extraction_and_cleaning() -> None:
    normalizer = TransactionNormalizer()
    enriched = normalizer.enrich(
        transaction=_tx(
            description="UPI/P2M/654547230671/MUNIYANDI C /haircu/YES BANK LIMITED YBS",
            amount=Decimal("-99.00"),
            tx_type="debit",
        ),
        account_holder_name="Abhinav B",
    )

    assert enriched.merchant_name == "MUNIYANDI C"
    assert enriched.clean_description == "Haircut"
    assert enriched.bank_gateway == "YES BANK LIMITED YBS"


def test_description_normalization_and_merchant_fallback() -> None:
    normalizer = TransactionNormalizer()

    investment = normalizer.enrich(
        transaction=_tx(
            description="UPI/P2M/617688132790/GROWW INVEST TECH PVT/Paid V/HDFC BANK LTD",
            amount=Decimal("-500.00"),
            tx_type="debit",
        ),
        account_holder_name=None,
    )

    assert investment.merchant_name == "GROWW INVEST TECH PVT"
    assert investment.clean_description == "Investment"
    assert investment.bank_gateway == "HDFC BANK LTD"

    fallback = normalizer.enrich(
        transaction=_tx(
            description="UPI/P2M/BP Petrol Pump/YES BANK LIMITED",
            amount=Decimal("-90.00"),
            tx_type="debit",
        ),
        account_holder_name=None,
    )

    assert fallback.merchant_name == "BP Petrol Pump"
    assert fallback.clean_description == "BP Petrol Pump"
    assert fallback.bank_gateway == "YES BANK LIMITED"


def test_merchant_extraction_ignores_bank_names_and_gateways() -> None:
    normalizer = TransactionNormalizer()
    enriched = normalizer.enrich(
        transaction=_tx(
            description="UPI/P2M/009918237600/BP Petrol Pump - PACR/petrol/AXIS BANK",
            amount=Decimal("-200.00"),
            tx_type="debit",
        ),
        account_holder_name=None,
    )

    assert enriched.merchant_name == "BP Petrol Pump"
    assert enriched.clean_description == "Petrol"
    assert enriched.bank_gateway == "AXIS BANK"


def test_category_mapping_fuel_investment_entertainment_income() -> None:
    normalizer = TransactionNormalizer()

    fuel = normalizer.enrich(
        transaction=_tx(
            description="UPI/P2M/BP Petrol Pump - PACR",
            amount=Decimal("-500.00"),
            tx_type="debit",
        ),
        account_holder_name=None,
    )
    assert fuel.category == "Fuel"

    investments = normalizer.enrich(
        transaction=_tx(
            description="UPI/P2M/GROWW SIP",
            amount=Decimal("-2000.00"),
            tx_type="debit",
        ),
        account_holder_name=None,
    )
    assert investments.category == "Investments"

    entertainment = normalizer.enrich(
        transaction=_tx(
            description="UPI/P2M/JioHotstar",
            amount=Decimal("-299.00"),
            tx_type="debit",
        ),
        account_holder_name=None,
    )
    assert entertainment.category == "Entertainment"

    income = normalizer.enrich(
        transaction=_tx(
            description="NEFT Salary Credit",
            amount=Decimal("35000.00"),
            tx_type="credit",
        ),
        account_holder_name=None,
    )
    assert income.category == "Income"
    assert income.is_income is True


def test_transfer_income_expense_detection() -> None:
    normalizer = TransactionNormalizer()

    transfer = normalizer.enrich(
        transaction=_tx(
            description="UPI Self Transfer ABHINAV B",
            amount=Decimal("-1000.00"),
            tx_type="debit",
        ),
        account_holder_name="Abhinav B",
    )
    assert transfer.is_internal_transfer is True
    assert transfer.normalized_transaction_type == "internal_transfer"
    assert transfer.is_expense is False
    assert transfer.category == "Transfer"

    income = normalizer.enrich(
        transaction=_tx(
            description="Payroll Salary Credit",
            amount=Decimal("20000.00"),
            tx_type="credit",
        ),
        account_holder_name="Abhinav B",
    )
    assert income.is_income is True
    assert income.normalized_transaction_type == "income"

    expense = normalizer.enrich(
        transaction=_tx(
            description="SOLAIMALAI FOOD PRODU",
            amount=Decimal("-250.00"),
            tx_type="debit",
        ),
        account_holder_name="Abhinav B",
    )
    assert expense.is_expense is True
    assert expense.normalized_transaction_type == "expense"