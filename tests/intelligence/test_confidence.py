from walletmind.intelligence.confidence import ConfidenceScorer


def test_confidence_score_caps_at_100() -> None:
    scorer = ConfidenceScorer()
    score = scorer.score(
        merchant_name="Swiggy",
        category="Food",
        payment_channel="UPI",
        is_recurring=True,
        is_transfer=True,
    )

    assert score == 100


def test_confidence_score_lower_for_unknowns() -> None:
    scorer = ConfidenceScorer()
    score = scorer.score(
        merchant_name=None,
        category="Others",
        payment_channel="Bank Transfer",
        is_recurring=False,
        is_transfer=False,
    )

    assert score == 15
