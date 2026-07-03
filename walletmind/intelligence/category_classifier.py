"""Deterministic category classifier."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryClassification:
    category: str
    subcategory: str | None
    transaction_kind: str


class CategoryClassifier:
    """Classifies transactions from merchant/description/channel text."""

    _CATEGORY_RULES: tuple[tuple[str, tuple[str, ...], str | None], ...] = (
        ("Salary", ("salary", "payroll"), "Income"),
        ("Investment", ("groww", "sip", "mutual", "zerodha"), "Investment"),
        ("Tax", ("tax", "tds", "gst", "income tax"), "Tax"),
        ("Fuel", ("petrol", "fuel", "diesel", "indian oil", "bp petrol"), "Fuel"),
        ("Food", ("swiggy", "zomato", "restaurant", "food"), "Dining"),
        ("Entertainment", ("netflix", "spotify", "hotstar", "youtube"), "Subscription"),
        ("Shopping", ("amazon", "flipkart", "shopping"), "Ecommerce"),
        ("Travel", ("uber", "ola", "metro", "rail", "trip"), "Commute"),
        ("Utilities", ("electricity", "water", "gas", "broadband", "internet"), "Utilities"),
        ("Insurance", ("insurance", "lic", "policy"), "Insurance"),
        ("Healthcare", ("hospital", "clinic", "medical", "pharmacy"), "Healthcare"),
        ("Education", ("school", "college", "tuition", "course"), "Education"),
        ("Rent", ("rent", "landlord"), "Rent"),
        ("ATM", ("atm",), "ATM"),
        ("Cash", ("cash",), "Cash"),
        ("Transfer", ("transfer", "imps", "neft", "rtgs"), "Transfer"),
        ("Bills", ("bill", "recharge"), "Bills"),
    )

    def classify(self, *, merchant_name: str | None, description: str, payment_channel: str, narration: str, is_transfer: bool) -> CategoryClassification:
        haystack = " ".join([merchant_name or "", description, payment_channel, narration]).lower()

        if is_transfer:
            return CategoryClassification(
                category="Transfer",
                subcategory="Internal" if "self" in haystack else "Bank Transfer",
                transaction_kind="transfer",
            )

        for category, keywords, subcategory in self._CATEGORY_RULES:
            if any(keyword in haystack for keyword in keywords):
                kind = "income" if category == "Salary" else "expense"
                return CategoryClassification(
                    category=category,
                    subcategory=subcategory,
                    transaction_kind=kind,
                )

        return CategoryClassification(
            category="Others",
            subcategory=None,
            transaction_kind="other",
        )
