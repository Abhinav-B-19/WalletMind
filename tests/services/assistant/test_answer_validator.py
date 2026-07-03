from __future__ import annotations

import pytest

from backend.app.services.assistant.answer_validator import AnswerValidator
from backend.app.services.assistant.context_builder import AssistantContext
from walletmind.exceptions import AssistantValidationError


def _context() -> AssistantContext:
    return AssistantContext(
        summary={
            "transaction_count": 4,
            "total_amount": 290.0,
            "average_amount": 72.5,
            "max_amount": 200.0,
            "min_amount": 20.0,
        },
        transactions=[
            {
                "transaction_id": "tx-1",
                "date": "2026-01-01",
                "merchant": "Starbucks",
                "category": "Food & Dining",
                "payment_channel": "Card",
                "transaction_type": "debit",
                "amount": -20.0,
                "is_recurring": False,
            },
            {
                "transaction_id": "tx-2",
                "date": "2026-01-15",
                "merchant": "Starbucks",
                "category": "Food & Dining",
                "payment_channel": "Card",
                "transaction_type": "debit",
                "amount": -30.0,
                "is_recurring": False,
            },
            {
                "transaction_id": "tx-3",
                "date": "2026-02-10",
                "merchant": "Uber",
                "category": "Transport",
                "payment_channel": "UPI",
                "transaction_type": "debit",
                "amount": -40.0,
                "is_recurring": False,
            },
            {
                "transaction_id": "tx-4",
                "date": "2026-02-20",
                "merchant": "Employer",
                "category": "Income",
                "payment_channel": "Bank Transfer",
                "transaction_type": "credit",
                "amount": 200.0,
                "is_recurring": True,
            },
        ],
    )


def test_validator_accepts_exact_transaction_amount() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="You spent $20.00 at Starbucks.",
        context=_context(),
    )


def test_validator_accepts_summed_amounts() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="Your total spending is $90.00 and total income is $200.00.",
        context=_context(),
    )


def test_validator_accepts_average_amount() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="Average transaction amount is $72.50.",
        context=_context(),
    )


def test_validator_accepts_category_total() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="Food & Dining total is $50.00.",
        context=_context(),
    )


def test_validator_accepts_merchant_total() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="You spent $50.00 at Starbucks.",
        context=_context(),
    )


def test_validator_accepts_monthly_total() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="February total spending is $40.00.",
        context=_context(),
    )


def test_validator_accepts_comparison_difference() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="Income exceeds spending by $110.00.",
        context=_context(),
    )


def test_validator_accepts_percentage_claim() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="Income contribution is 68.97% of total activity.",
        context=_context(),
    )


def test_validator_rejects_unsupported_amount() -> None:
    validator = AnswerValidator()

    with pytest.raises(AssistantValidationError, match="not derivable"):
        validator.validate(
            answer="You spent $999.99 at Starbucks.",
            context=_context(),
        )


def test_validator_rejects_unsupported_merchant() -> None:
    validator = AnswerValidator()

    with pytest.raises(AssistantValidationError, match="merchants"):
        validator.validate(
            answer="You spent $50.00 at McDonalds.",
            context=_context(),
        )


def test_validator_rejects_unsupported_transaction_reference() -> None:
    validator = AnswerValidator()

    with pytest.raises(AssistantValidationError, match="transactions"):
        validator.validate(
            answer="Transaction tx-999 shows a debit of $20.00.",
            context=_context(),
        )


def test_validator_rejects_unsupported_iso_date() -> None:
    validator = AnswerValidator()

    with pytest.raises(AssistantValidationError, match="dates"):
        validator.validate(
            answer="On 2026-03-01 you spent $20.00 at Starbucks.",
            context=_context(),
        )


def test_validator_rejects_unsupported_month_reference() -> None:
    validator = AnswerValidator()

    with pytest.raises(AssistantValidationError, match="months"):
        validator.validate(
            answer="March spending was $20.00.",
            context=_context(),
        )


def test_validator_allows_unavailable_answers() -> None:
    validator = AnswerValidator()
    validator.validate(
        answer="I cannot determine that from the available transactions.",
        context=_context(),
    )
