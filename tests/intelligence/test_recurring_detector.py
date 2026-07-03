from walletmind.intelligence.recurring_detector import RecurringDetector


def test_recurring_detector_subscription() -> None:
    detector = RecurringDetector()
    result = detector.detect(
        narration="NETFLIX monthly",
        description="subscription",
        merchant_name="Netflix",
    )

    assert result.is_subscription is True
    assert result.is_recurring is True


def test_recurring_detector_salary_recurring() -> None:
    detector = RecurringDetector()
    result = detector.detect(
        narration="Salary credit",
        description="salary",
        merchant_name="Employer",
    )

    assert result.is_recurring is True
