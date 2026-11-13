import pytest

from swiss_ai_hub.core.generative_ai.document.classification.amount_text_parser import AmountTextParser

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "amount"),
    [
        ("CHF 12'496.36", 12496.36),
        ("CHF 12’496.36", 12496.36),
        ("12.496,36 €", 12496.36),
        ("EUR 12 496,36", 12496.36),
        ("CHF 12 496,36", 12496.36),
        ("$12,496.36", 12496.36),
        ("12496.36", 12496.36),
        ("Total CHF 12'496.36", 12496.36),
        ("Fr. 1'250.–", 1250.0),
        ("Fr. 1'250.-", 1250.0),
        ("1.234", 1234.0),
        ("1,5", 1.5),
        ("CHF 0.95", 0.95),
    ],
)
def test_every_separator_convention_reads_the_same_amount(raw: str, amount: float) -> None:
    assert AmountTextParser.parse(raw) == amount


@pytest.mark.parametrize("raw", ["-500.00", "CHF -500.00", "−CHF 500.00", "500.00-", "(CHF 500.00)"])
def test_a_negative_total_keeps_its_sign(raw: str) -> None:
    assert AmountTextParser.parse(raw) == -500.0


@pytest.mark.parametrize("raw", ["", "gratis", None])
def test_text_without_a_number_is_no_amount(raw: str | None) -> None:
    assert AmountTextParser.parse(raw) is None
