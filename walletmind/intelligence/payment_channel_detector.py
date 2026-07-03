"""Deterministic payment channel detector."""

from __future__ import annotations


class PaymentChannelDetector:
    """Maps narration text to payment channel via keyword priority."""

    _RULES: tuple[tuple[str, str], ...] = (
        ("salary", "Salary Credit"),
        ("interest", "Interest Credit"),
        ("standing instruction", "Standing Instruction"),
        ("si ", "Standing Instruction"),
        ("rtgs", "RTGS"),
        ("neft", "NEFT"),
        ("imps", "IMPS"),
        ("upi", "UPI"),
        ("atm", "ATM"),
        ("debit card", "Debit Card"),
        ("credit card", "Credit Card"),
        ("cheque", "Cheque"),
        ("cash", "Cash"),
        ("transfer", "Bank Transfer"),
    )

    def detect(self, *, narration: str, description: str) -> str:
        haystack = f"{narration} {description}".lower()
        for keyword, channel in self._RULES:
            if keyword in haystack:
                return channel
        return "Bank Transfer"
