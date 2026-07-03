"""Build compact retrieval-grounded assistant context for AI prompts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import mean
from typing import Any

from backend.app.services.assistant.retrieval_service import RetrievalResult


@dataclass(frozen=True)
class AssistantContext:
    """Compact assistant context payload for prompt generation and source mapping."""

    summary: dict[str, Any]
    transactions: list[dict[str, Any]]


class ContextBuilder:
    """Convert retrieval output into compact and safe AI context."""

    def build(self, retrieval: RetrievalResult) -> AssistantContext:
        """Create summary + transaction snippets suitable for model context windows."""

        transactions = retrieval.transactions
        amounts = [abs(Decimal(tx.amount)) for tx in transactions]

        summary = {
            "statement_id": str(retrieval.statement_uuid),
            "question": retrieval.question,
            "filters_applied": retrieval.filters_applied,
            "transaction_count": len(transactions),
            "total_amount": float(sum(amounts, Decimal("0"))),
            "average_amount": float(mean(amounts)) if amounts else 0.0,
            "max_amount": float(max(amounts)) if amounts else 0.0,
            "min_amount": float(min(amounts)) if amounts else 0.0,
        }

        # Keep snippets compact and non-sensitive while preserving traceability.
        snippets = [
            {
                "transaction_id": str(tx.transaction_uuid),
                "date": tx.transaction_date.isoformat(),
                "merchant": (tx.merchant_name or "Unknown")[:120],
                "category": tx.category,
                "payment_channel": tx.payment_channel,
                "transaction_type": tx.transaction_type,
                "amount": float(tx.amount),
                "is_recurring": bool((tx.flags or {}).get("is_recurring")),
            }
            for tx in transactions[:30]
        ]

        return AssistantContext(summary=summary, transactions=snippets)
