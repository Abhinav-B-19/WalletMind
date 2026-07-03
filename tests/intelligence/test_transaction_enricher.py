from datetime import date
from decimal import Decimal

from walletmind.intelligence.transaction_enricher import TransactionEnricher
from walletmind.schemas.transaction import TransactionCreateDTO


def _tx(description: str) -> TransactionCreateDTO:
    return TransactionCreateDTO(
        transaction_date=date(2026, 7, 3),
        description=description,
        amount=Decimal("-120.00"),
        transaction_type="debit",
        raw_row_json={"row": 1},
        clean_description="Haircut",
    )


def test_transaction_enricher_pipeline_populates_fields() -> None:
    enricher = TransactionEnricher()
    result = enricher.enrich(
        transaction=_tx("UPI/P2M/654547230671/MUNIYANDI C /haircu/YES BANK LIMITED YBS"),
        account_holder_name="Alex Doe",
    )

    assert result.merchant_name == "Muniyandi C"
    assert result.bank_gateway == "YES BANK LIMITED YBS"
    assert result.payment_channel == "UPI"
    assert result.category in {"Others", "Food", "Fuel", "Entertainment", "Shopping", "Utilities", "Transfer", "Investment", "Tax", "Salary", "Travel", "Bills", "Insurance", "Healthcare", "Education", "Rent", "ATM", "Cash"}
    assert result.confidence_score >= 0


def test_enrichment_is_idempotent() -> None:
    enricher = TransactionEnricher()
    tx = _tx("UPI/P2M/999/NETFLIX/YES BANK")

    one = enricher.enrich(transaction=tx, account_holder_name=None)
    two = enricher.enrich(transaction=tx, account_holder_name=None)

    assert one == two
