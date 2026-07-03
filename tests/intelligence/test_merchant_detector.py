from walletmind.intelligence.merchant_detector import MerchantDetector


def test_merchant_detector_extracts_merchant_and_gateway() -> None:
    detector = MerchantDetector()
    result = detector.detect(
        narration="UPI/P2M/654547230671/MUNIYANDI C /haircu/YES BANK LIMITED YBS"
    )

    assert result.merchant_name == "Muniyandi C"
    assert result.bank_gateway == "YES BANK LIMITED YBS"


def test_merchant_detector_alias_mapping() -> None:
    detector = MerchantDetector()
    result = detector.detect(
        narration="UPI/P2M/92349382/GOOGLE IN/PLAY STORE/YES BANK"
    )

    assert result.merchant_name == "Google Play"
