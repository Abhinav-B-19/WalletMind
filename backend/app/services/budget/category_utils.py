"""Budget category classification helpers."""

from __future__ import annotations

import re

_INCOME_CATEGORY_EXACT = {
    "income",
    "salary",
    "interest",
    "refund",
    "cashback",
    "cash back",
    "dividend",
    "credit",
    "credits",
}

_INCOME_CATEGORY_TOKENS = {
    "income",
    "salary",
    "interest",
    "refund",
    "cashback",
    "dividend",
}


def is_expense_category(category: str | None) -> bool:
    """Return True when a category should be treated as expense-only for budgeting."""

    if category is None:
        return True

    normalized = re.sub(r"\s+", " ", category.strip().lower())
    if not normalized:
        return True

    if normalized in _INCOME_CATEGORY_EXACT:
        return False

    tokens = [token for token in re.split(r"[^a-z]+", normalized) if token]
    if any(token in _INCOME_CATEGORY_TOKENS for token in tokens):
        return False

    return True
