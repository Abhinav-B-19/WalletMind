"""Deterministic spending summary construction for AI insight generation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean
from typing import Any
from uuid import UUID

from walletmind.schemas.transaction import TransactionDTO


@dataclass(frozen=True)
class SpendingSummary:
    """Deterministic metrics computed from enriched transactions."""

    statement_uuid: UUID
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    savings_rate: float
    category_totals: dict[str, Decimal]
    top_spending_categories: list[dict[str, Any]]
    top_merchants: list[dict[str, Any]]
    largest_expense: dict[str, Any] | None
    largest_income: dict[str, Any] | None
    monthly_averages: dict[str, float]
    monthly_trend: list[dict[str, Any]]
    recurring_subscriptions: list[dict[str, Any]]
    transaction_count: int
    credit_count: int
    debit_count: int

    def as_prompt_payload(self) -> dict[str, Any]:
        """Convert summary to a compact JSON-serializable payload for prompting."""

        return {
            "statement_uuid": str(self.statement_uuid),
            "transaction_count": self.transaction_count,
            "credit_count": self.credit_count,
            "debit_count": self.debit_count,
            "cash_flow": {
                "total_income": float(self.total_income),
                "total_expenses": float(self.total_expenses),
                "net_cash_flow": float(self.net_cash_flow),
                "savings_rate": self.savings_rate,
            },
            "category_breakdown": {
                key: float(value) for key, value in self.category_totals.items()
            },
            "top_spending_categories": self.top_spending_categories,
            "top_merchants": self.top_merchants,
            "largest_expense": self.largest_expense,
            "largest_income": self.largest_income,
            "monthly_averages": self.monthly_averages,
            "monthly_trend": self.monthly_trend,
            "recurring_subscriptions": self.recurring_subscriptions,
        }


class SpendingSummaryBuilder:
    """Build deterministic summary statistics for statement transactions."""

    def build(
        self,
        *,
        statement_uuid: UUID,
        transactions: list[TransactionDTO],
    ) -> SpendingSummary:
        """Construct deterministic financial metrics for AI-context input."""

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        category_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        merchant_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        monthly_income: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        monthly_expense: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        subscription_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        largest_expense_tx: TransactionDTO | None = None
        largest_income_tx: TransactionDTO | None = None

        credit_count = 0
        debit_count = 0

        for tx in transactions:
            amount = Decimal(tx.amount)
            abs_amount = abs(amount)
            month_key = tx.transaction_date.strftime("%Y-%m")
            flags = tx.flags or {}

            if tx.transaction_type.lower() == "credit":
                credit_count += 1
            elif tx.transaction_type.lower() == "debit":
                debit_count += 1

            is_income = bool(flags.get("is_income")) or amount > 0
            is_expense = bool(flags.get("is_expense")) or amount < 0

            if is_income:
                total_income += abs_amount
                monthly_income[month_key] += abs_amount
                if (
                    largest_income_tx is None
                    or abs_amount > abs(largest_income_tx.amount)
                ):
                    largest_income_tx = tx

            if is_expense:
                total_expenses += abs_amount
                monthly_expense[month_key] += abs_amount
                category = tx.category or "Others"
                category_totals[category] += abs_amount
                merchant_key = (tx.merchant_name or "Unknown").strip() or "Unknown"
                merchant_totals[merchant_key] += abs_amount
                if (
                    largest_expense_tx is None
                    or abs_amount > abs(largest_expense_tx.amount)
                ):
                    largest_expense_tx = tx

            if bool(flags.get("is_subscription")):
                merchant_key = (tx.merchant_name or "Unknown").strip() or "Unknown"
                subscription_totals[merchant_key] += abs_amount

        net_cash_flow = total_income - total_expenses
        savings_rate = (
            round(float((net_cash_flow / total_income) * Decimal("100")), 2)
            if total_income > 0
            else 0.0
        )

        top_spending_categories = [
            {"category": category, "amount": float(amount)}
            for category, amount in sorted(
                category_totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:5]
        ]

        top_merchants = [
            {"merchant": merchant, "amount": float(amount)}
            for merchant, amount in sorted(
                merchant_totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:10]
        ]

        month_keys = sorted({*monthly_income.keys(), *monthly_expense.keys()})
        monthly_trend = [
            {
                "month": month_key,
                "income": float(monthly_income.get(month_key, Decimal("0"))),
                "expenses": float(monthly_expense.get(month_key, Decimal("0"))),
                "net": float(
                    monthly_income.get(month_key, Decimal("0"))
                    - monthly_expense.get(month_key, Decimal("0"))
                ),
            }
            for month_key in month_keys
        ]

        avg_income = (
            mean([item["income"] for item in monthly_trend])
            if monthly_trend
            else 0.0
        )
        avg_expenses = (
            mean([item["expenses"] for item in monthly_trend])
            if monthly_trend
            else 0.0
        )
        avg_net = (
            mean([item["net"] for item in monthly_trend])
            if monthly_trend
            else 0.0
        )

        recurring_subscriptions = [
            {"merchant": merchant, "amount": float(amount)}
            for merchant, amount in sorted(
                subscription_totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        return SpendingSummary(
            statement_uuid=statement_uuid,
            total_income=total_income,
            total_expenses=total_expenses,
            net_cash_flow=net_cash_flow,
            savings_rate=savings_rate,
            category_totals=dict(category_totals),
            top_spending_categories=top_spending_categories,
            top_merchants=top_merchants,
            largest_expense=self._build_largest_transaction_snapshot(largest_expense_tx),
            largest_income=self._build_largest_transaction_snapshot(largest_income_tx),
            monthly_averages={
                "income": round(avg_income, 2),
                "expenses": round(avg_expenses, 2),
                "net": round(avg_net, 2),
            },
            monthly_trend=monthly_trend,
            recurring_subscriptions=recurring_subscriptions,
            transaction_count=len(transactions),
            credit_count=credit_count,
            debit_count=debit_count,
        )

    @staticmethod
    def _build_largest_transaction_snapshot(
        tx: TransactionDTO | None,
    ) -> dict[str, Any] | None:
        """Return minimal, non-sensitive details for largest-transaction highlights."""

        if tx is None:
            return None

        merchant = (tx.merchant_name or "Unknown").strip() or "Unknown"
        return {
            "date": tx.transaction_date.isoformat(),
            "amount": float(abs(Decimal(tx.amount))),
            "category": tx.category,
            "merchant": merchant,
        }
