import pytest

from swiss_ai_hub.core.generative_ai.document.classification.currency_text_parser import CurrencyTextParser

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("CHF", "CHF"),
        ("Fr.", "CHF"),
        ("SFr. 20.00", "CHF"),
        ("CHF 12'496.36", "CHF"),
        ("12.496,36 €", "EUR"),
        ("Euro", "EUR"),
        ("US$ 50", "USD"),
        ("£20", "GBP"),
        ("SEK", "SEK"),
    ],
)
def test_codes_symbols_and_swiss_abbreviations_are_read(raw: str, code: str) -> None:
    assert CurrencyTextParser.parse(raw) == code


@pytest.mark.parametrize("raw", ["$ 50", "12'496.36", "", None])
def test_a_bare_dollar_or_no_currency_stays_unread(raw: str | None) -> None:
    assert CurrencyTextParser.parse(raw) is None
