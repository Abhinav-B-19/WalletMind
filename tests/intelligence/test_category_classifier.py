from walletmind.intelligence.category_classifier import CategoryClassifier


def test_category_classifier_food() -> None:
    classifier = CategoryClassifier()
    result = classifier.classify(
        merchant_name="Swiggy",
        description="Dinner order",
        payment_channel="UPI",
        narration="UPI/P2M/Swiggy",
        is_transfer=False,
    )

    assert result.category == "Food"
    assert result.transaction_kind == "expense"


def test_category_classifier_transfer_priority() -> None:
    classifier = CategoryClassifier()
    result = classifier.classify(
        merchant_name=None,
        description="self transfer",
        payment_channel="IMPS",
        narration="IMPS SELF TRANSFER",
        is_transfer=True,
    )

    assert result.category == "Transfer"
    assert result.transaction_kind == "transfer"
