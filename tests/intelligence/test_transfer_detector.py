from walletmind.intelligence.transfer_detector import TransferDetector


def test_transfer_detector_marks_internal_transfer() -> None:
    detector = TransferDetector()
    result = detector.detect(
        narration="UPI Self Transfer",
        description="to self",
        merchant_name="Alex Doe",
        account_holder_name="Alex Doe",
    )

    assert result.is_transfer is True
    assert result.is_internal_transfer is True


def test_transfer_detector_marks_regular_transfer() -> None:
    detector = TransferDetector()
    result = detector.detect(
        narration="NEFT transfer",
        description="rent transfer",
        merchant_name="Landlord",
        account_holder_name="Alex Doe",
    )

    assert result.is_transfer is True
