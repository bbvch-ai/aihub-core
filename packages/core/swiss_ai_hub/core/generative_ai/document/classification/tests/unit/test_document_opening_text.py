import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_opening_text import DocumentOpeningText
from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK

pytestmark = pytest.mark.unit


def _pages(*pages: str) -> str:
    return f"\n{PAGE_BREAK}\n".join(pages)


def test_a_short_document_is_read_whole() -> None:
    text = _pages("# Rechnung RE-1", "Total CHF 100.00")

    assert DocumentOpeningText.of(text) == "# Rechnung RE-1\n\nTotal CHF 100.00"


def test_a_long_document_is_read_from_its_first_pages_and_its_end() -> None:
    middle = "Positionen 41-80\n" + "| 41 | Kabel | 1 | 9.90 |\n" * 100
    text = _pages("# Rechnung RE-1", "Positionen 1-40", middle, "Total CHF 100.00\nZahlbar innert 30 Tagen")

    excerpt = DocumentOpeningText.of(text)

    assert excerpt.startswith("# Rechnung RE-1\n\nPositionen 1-40")
    assert "Positionen 41-80" not in excerpt
    assert DocumentOpeningText.GAP in excerpt
    assert excerpt.endswith("Zahlbar innert 30 Tagen")


def test_the_end_of_a_document_that_goes_little_beyond_its_opening_is_read_whole() -> None:
    text = _pages("# Rechnung RE-1", "Positionen 1-40", "Positionen 41-80", "Total CHF 100.00")

    assert DocumentOpeningText.of(text).endswith("Positionen 41-80\n\nTotal CHF 100.00")


def test_a_document_without_page_breaks_is_cut_by_characters() -> None:
    paragraph = "Lorem ipsum dolor sit amet. " * 20
    text = "\n\n".join([paragraph] * 40) + "\n\nTotal CHF 100.00"

    excerpt = DocumentOpeningText.of(text)
    opening = excerpt.split(DocumentOpeningText.GAP)[0]

    assert len(opening) <= DocumentOpeningText.MAX_OPENING_CHARACTERS
    assert opening.endswith(paragraph.strip())
    assert excerpt.endswith("Total CHF 100.00")
    assert len(excerpt) < DocumentOpeningText.MAX_OPENING_CHARACTERS + DocumentOpeningText.TAIL_CHARACTERS + 20
