from swiss_ai_hub.core.generative_ai.document.extraction.document_title_deriver import DocumentTitleDeriver

_HEADED = "# Mandatsvereinbarung 2026-0042\n\nDie Buchhaltung wird gefuehrt."


def test_subject_wins_over_a_heading():
    """A mail states its own title; a heading in its body is only an inference about one."""
    assert DocumentTitleDeriver.derive(_HEADED, "anfrage.eml", subject="Rechnung 2026-0042") == "Rechnung 2026-0042"


def test_blank_subject_falls_through_to_the_heading():
    assert DocumentTitleDeriver.derive(_HEADED, "x.pdf", subject="   ") == "Mandatsvereinbarung 2026-0042"


def test_heading_wins_over_the_filename():
    assert DocumentTitleDeriver.derive(_HEADED, "2f8c-final-v2.pdf") == "Mandatsvereinbarung 2026-0042"


def test_a_deeper_heading_still_counts():
    """MinerU labels a scan's title by visual prominence, which is not always level 1."""
    assert DocumentTitleDeriver.derive("## Rechnung 42\n\nBetrag.", "x.pdf") == "Rechnung 42"


def test_falls_back_to_the_filename_stem_without_the_extension():
    assert DocumentTitleDeriver.derive("Betrag: CHF 4250.", "invoice-2026.pdf") == "invoice-2026"


def test_an_empty_heading_is_not_a_title():
    assert DocumentTitleDeriver.derive("#\n\nBetrag.", "invoice.pdf") == "invoice"


def test_subject_is_trimmed():
    assert DocumentTitleDeriver.derive("", "x.eml", subject="  Rechnung  ") == "Rechnung"
