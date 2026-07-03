"""Confidence scoring for deterministic enrichment."""

from __future__ import annotations


class ConfidenceScorer:
    """Scores enrichment confidence on a fixed 0-100 scale."""

    def score(
        self,
        *,
        merchant_name: str | None,
        category: str,
        payment_channel: str,
        is_recurring: bool,
        is_transfer: bool,
    ) -> int:
        score = 0

        if merchant_name:
            score += 40
        if category != "Others":
            score += 25
        if payment_channel:
            score += 15
        if is_recurring:
            score += 10
        if is_transfer:
            score += 10

        return min(score, 100)
