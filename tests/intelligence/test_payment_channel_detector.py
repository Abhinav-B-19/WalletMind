from walletmind.intelligence.payment_channel_detector import PaymentChannelDetector


def test_payment_channel_detects_upi() -> None:
    detector = PaymentChannelDetector()
    channel = detector.detect(
        narration="UPI/P2M/abc",
        description="upi payment",
    )
    assert channel == "UPI"


def test_payment_channel_detects_salary_credit() -> None:
    detector = PaymentChannelDetector()
    channel = detector.detect(
        narration="NEFT Salary credit",
        description="Salary",
    )
    assert channel == "Salary Credit"
