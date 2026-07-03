"""Deterministic recurring and subscription detector."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecurringDetectionResult:
    is_subscription: bool
    is_recurring: bool


class RecurringDetector:
    """Detects recurring patterns from known entities and keywords."""

    _SUBSCRIPTION_KEYWORDS = (
        "netflix",
        "spotify",
        "hotstar",
        "subscription",
        "broadband",
        "internet",
        "mobile recharge",
    )

    _RECURRING_KEYWORDS = _SUBSCRIPTION_KEYWORDS + (
        "salary",
        "rent",
        "electricity",
        "insurance",
        "lic",
        "sip",
        "mutual fund",
    )

    def detect(self, *, narration: str, description: str, merchant_name: str | None) -> RecurringDetectionResult:
        haystack = f"{narration} {description} {merchant_name or ''}".lower()
        is_subscription = any(keyword in haystack for keyword in self._SUBSCRIPTION_KEYWORDS)
        is_recurring = any(keyword in haystack for keyword in self._RECURRING_KEYWORDS)
        return RecurringDetectionResult(
            is_subscription=is_subscription,
            is_recurring=is_recurring,
        )
