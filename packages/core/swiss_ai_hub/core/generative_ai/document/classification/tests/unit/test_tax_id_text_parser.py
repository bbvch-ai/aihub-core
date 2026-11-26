"""Tax IDs: one stored form, and a Swiss UID only when its check digit holds, since a misread digit would name
another company. CHE-123.456.788 is a valid UID by the modulus-11 rule; CHE-123.456.789 is not."""

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.tax_id_text_parser import TaxIdTextParser

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "raw",
    [
        "CHE-123.456.788",
        "CHE-123.456.788 MWST",
        "CHE-123.456.788 TVA",
        "CHE-123.456.788 IVA",
        "CHE123456788",
        "UID: CHE-123.456.788",
        "MWST-Nr. CHE-123.456.788 MWST",
    ],
)
def test_a_swiss_uid_is_read_without_separators_or_suffix(raw: str) -> None:
    assert TaxIdTextParser.parse(raw) == "CHE123456788"


def test_a_swiss_uid_that_fails_its_check_digit_stays_unread() -> None:
    assert TaxIdTextParser.parse("CHE-123.456.789 MWST") is None


@pytest.mark.parametrize(
    ("raw", "stored"),
    [
        ("USt-IdNr.: DE 123 456 789", "DE123456789"),
        ("DE123456789", "DE123456789"),
        ("ATU12345678", "ATU12345678"),
        ("TVA intracommunautaire FR 12 345678901", "FR12345678901"),
        ("P.IVA IT 12345678901", "IT12345678901"),
        ("NL123456789B01", "NL123456789B01"),
    ],
)
def test_an_eu_vat_number_is_read_in_its_country_format(raw: str, stored: str) -> None:
    assert TaxIdTextParser.parse(raw) == stored


@pytest.mark.parametrize("raw", ["Steuernummer 12/345/67890", "DE 1234", "HRB 12345", "", None])
def test_a_tax_office_number_or_malformed_id_stays_unread(raw: str | None) -> None:
    assert TaxIdTextParser.parse(raw) is None
