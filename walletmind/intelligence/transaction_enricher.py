"""Transaction intelligence orchestration pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from walletmind.schemas.transaction import TransactionCreateDTO
from walletmind.intelligence.category_classifier import CategoryClassifier
from walletmind.intelligence.confidence import ConfidenceScorer
from walletmind.intelligence.merchant_detector import MerchantDetector
from walletmind.intelligence.payment_channel_detector import PaymentChannelDetector
from walletmind.intelligence.recurring_detector import RecurringDetector
from walletmind.intelligence.transfer_detector import TransferDetector


@dataclass(frozen=True)
class IntelligenceResult:
    merchant_name: str | None
    bank_gateway: str | None
    category: str
    subcategory: str | None
    payment_channel: str
    transaction_kind: str
    confidence_score: int
    is_transfer: bool
    is_internal_transfer: bool
    is_subscription: bool
    is_recurring: bool
    is_salary: bool
    is_cash: bool
    is_atm: bool
    is_loan: bool
    is_investment: bool
    is_tax: bool


class TransactionEnricher:
    """Deterministic transaction intelligence engine."""

    def __init__(self) -> None:
        self._merchant_detector = MerchantDetector()
        self._category_classifier = CategoryClassifier()
        self._payment_channel_detector = PaymentChannelDetector()
        self._transfer_detector = TransferDetector()
        self._recurring_detector = RecurringDetector()
        self._confidence_scorer = ConfidenceScorer()

    def enrich(self, *, transaction: TransactionCreateDTO, account_holder_name: str | None) -> IntelligenceResult:
        narration = transaction.description
        description = (transaction.clean_description or transaction.description).strip()

        merchant = self._merchant_detector.detect(narration=narration)
        payment_channel = self._payment_channel_detector.detect(
            narration=narration,
            description=description,
        )
        transfer = self._transfer_detector.detect(
            narration=narration,
            description=description,
            merchant_name=merchant.merchant_name,
            account_holder_name=account_holder_name,
        )
        recurring = self._recurring_detector.detect(
            narration=narration,
            description=description,
            merchant_name=merchant.merchant_name,
        )
        category = self._category_classifier.classify(
            merchant_name=merchant.merchant_name,
            description=description,
            payment_channel=payment_channel,
            narration=narration,
            is_transfer=transfer.is_transfer,
        )

        is_salary = category.category == "Salary" or payment_channel == "Salary Credit"
        is_cash = category.category == "Cash" or payment_channel == "Cash"
        is_atm = category.category == "ATM" or payment_channel == "ATM"
        is_investment = category.category == "Investment"
        is_tax = category.category == "Tax"
        is_loan = "loan" in f"{narration} {description}".lower()

        confidence_score = self._confidence_scorer.score(
            merchant_name=merchant.merchant_name,
            category=category.category,
            payment_channel=payment_channel,
            is_recurring=recurring.is_recurring,
            is_transfer=transfer.is_transfer,
        )

        return IntelligenceResult(
            merchant_name=merchant.merchant_name,
            bank_gateway=merchant.bank_gateway,
            category=category.category,
            subcategory=category.subcategory,
            payment_channel=payment_channel,
            transaction_kind=category.transaction_kind,
            confidence_score=confidence_score,
            is_transfer=transfer.is_transfer,
            is_internal_transfer=transfer.is_internal_transfer,
            is_subscription=recurring.is_subscription,
            is_recurring=recurring.is_recurring,
            is_salary=is_salary,
            is_cash=is_cash,
            is_atm=is_atm,
            is_loan=is_loan,
            is_investment=is_investment,
            is_tax=is_tax,
        )
