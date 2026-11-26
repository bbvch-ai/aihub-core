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


def test_a_long_contract_is_read_with_its_term_court_and_signing_clauses_from_the_middle() -> None:
    filler = "\n".join(f"{number}.1 Die Lizenzgeberin erbringt die Leistung gemäss Anhang." for number in range(3, 60))
    middle = (
        f"{filler}\nArt. 16 Vertragsdauer\n16.1 Die Vertragslaufzeit beginnt am 1. Januar 2024 und dauert bis zum "
        f"31. Dezember 2026.\n{filler}\nArt. 19 Gerichtsstand\nAusschliesslicher Gerichtsstand ist Zug.\n"
        f"Zug, 28. November 2023 Zürich, 28. November 2023\n{filler}"
    )
    text = _pages("# Lizenzvertrag LV-1", "Art. 1 Gegenstand", middle, "Anhang C Preise\nTotal CHF 9'000.00")

    excerpt = DocumentOpeningText.of(text)

    assert "16.1 Die Vertragslaufzeit beginnt am 1. Januar 2024" in excerpt
    assert "Ausschliesslicher Gerichtsstand ist Zug." in excerpt
    assert "Zug, 28. November 2023" in excerpt
    assert excerpt.endswith("Total CHF 9'000.00")
    assert len(excerpt) < 4000


def test_a_mention_of_the_term_in_passing_gives_way_to_its_heading() -> None:
    passing = "Die Lizenz gilt für die Vertragsdauer und umfasst alle Updates, die während dieser Zeit erscheinen."
    filler = "\n".join(f"Ziffer {number} regelt die Einzelheiten der Wartung und des Supports." for number in range(80))
    middle = f"{passing}\n{passing}\n{filler}\nArt. 9 Vertragsdauer\nDer Vertrag läuft bis 30. Juni 2027.\n{filler}"
    text = _pages("# Vertrag", "Art. 1", middle, "Unterschriften")

    assert "Der Vertrag läuft bis 30. Juni 2027." in DocumentOpeningText.of(text)
