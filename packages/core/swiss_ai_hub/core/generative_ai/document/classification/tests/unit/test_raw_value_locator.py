import pytest

from swiss_ai_hub.core.generative_ai.document.classification.raw_value_locator import RawValueLocator

pytestmark = pytest.mark.unit

_TEXT = """# Hooli AG
**Total CHF 12’496.36**
Leistungszeitraum: 1.–28.2.2025
Rechnung RE\\-2025\\-0412
"""


@pytest.mark.parametrize(
    "raw",
    ["Hooli AG", "hooli ag", "CHF 12'496.36", "1.-28.2.2025", "RE-2025-0412", "Hooli  AG", "HooliAG"],
)
def test_a_copy_differing_in_case_quotes_dashes_emphasis_or_spacing_is_found(raw: str) -> None:
    assert RawValueLocator.appears_in(raw, _TEXT)


@pytest.mark.parametrize("raw", ["Hooli GmbH", "CHF 12'496.37", "  "])
def test_a_value_that_is_not_in_the_document_is_not_found(raw: str) -> None:
    assert not RawValueLocator.appears_in(raw, _TEXT)
