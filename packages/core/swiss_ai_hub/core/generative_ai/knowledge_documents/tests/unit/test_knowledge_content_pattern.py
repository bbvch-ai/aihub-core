import unicodedata

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_search_pattern_error import InvalidSearchPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_line import KnowledgeContentLine
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_pattern import KnowledgeContentPattern
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_limits import (
    KnowledgeContentSearchLimits,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget

pytestmark = pytest.mark.unit


def _lines(pattern: KnowledgeContentPattern, text: str, **limits: int) -> tuple[list[KnowledgeContentLine], int]:
    return pattern.matching_lines(text, KnowledgeContentSearchLimits(**limits), KnowledgeSearchBudget(5))


@pytest.mark.parametrize("term", ["ORDER-4711-XQ", "a.b", "(draft)", "C++", "#1", "CHF 1'250.00", "x{2}", "^$|"])
def test_an_exact_term_matches_only_itself(term: str) -> None:
    pattern = KnowledgeContentPattern(term)

    lines, count = _lines(pattern, f"before\nsee {term} here\nafter")

    assert count == 1
    assert lines[0].text == f"see {term} here"


def test_regex_characters_in_an_exact_term_are_not_special() -> None:
    assert _lines(KnowledgeContentPattern("a.b"), "axb\na+b")[1] == 0


def test_the_database_pattern_is_unicode_aware_and_multiline() -> None:
    insensitive = KnowledgeContentPattern("RFC 9000")
    sensitive = KnowledgeContentPattern(r"RFC\s+9000", is_regex=True, case_sensitive=True)

    assert (insensitive.database_pattern, insensitive.database_options) == ("(*UCP)RFC 9000", "mi")
    assert (sensitive.database_pattern, sensitive.database_options) == (r"(*UCP)RFC\s+9000", "m")


def test_a_term_with_umlauts_is_also_searched_decomposed() -> None:
    pattern = KnowledgeContentPattern("Prüfbericht")

    assert pattern.database_pattern == f"(*UCP)(?:Prüfbericht)|(?:{unicodedata.normalize('NFD', 'Prüfbericht')})"


@pytest.mark.parametrize(
    ("query", "is_regex", "reason"),
    [
        ("", False, "empty"),
        ("x" * 501, False, "longer than 500"),
        ("a\0b", False, "NUL"),
        ("invoices/(2025", True, "escape literal characters"),
        ("a*", True, "matches empty text"),
        ("^", True, "matches empty text"),
        ("(?:Lieferung){e<=1}", True, "fuzzy constraints"),
    ],
)
def test_an_unusable_query_is_rejected_with_a_hint(query: str, is_regex: bool, reason: str) -> None:
    with pytest.raises(InvalidSearchPatternError, match=reason):
        KnowledgeContentPattern(query, is_regex=is_regex)


def test_a_literal_brace_quantifier_is_not_mistaken_for_a_fuzzy_constraint() -> None:
    assert _lines(KnowledgeContentPattern(r"ORDER-\d{4}-[A-Z]{2}", is_regex=True), "ORDER-4711-XQ")[1] == 1


def test_lines_are_numbered_and_located_by_offset_into_the_stored_text() -> None:
    text = "intro\nRFC 9000 first\nmiddle\nlast RFC 9000 and RFC 9000"
    lines, count = _lines(KnowledgeContentPattern("rfc 9000"), text)

    assert count == 2
    assert [(line.line_number, line.text) for line in lines] == [
        (2, "RFC 9000 first"),
        (4, "last RFC 9000 and RFC 9000"),
    ]
    assert all(text[line.start : line.end] == line.text for line in lines)


def test_offsets_fit_decomposed_text_searched_with_a_composed_term() -> None:
    text = unicodedata.normalize("NFD", "Kopf\nDer Prüfbericht liegt vor.\nÜbergabe")
    lines, count = _lines(KnowledgeContentPattern("prüfbericht"), text)

    assert count == 1
    assert lines[0].line_number == 2
    assert text[lines[0].start : lines[0].end] == lines[0].text
    assert unicodedata.normalize("NFC", lines[0].text) == "Der Prüfbericht liegt vor."


def test_a_decomposed_character_class_does_not_match_the_plain_letter() -> None:
    """`[ü]` decomposes into a class holding `u`; only the composed check stops it from matching `Prufbericht`."""
    lines, count = _lines(KnowledgeContentPattern("Pr[ü]fbericht", is_regex=True), "Prufbericht\nPrüfbericht")

    assert count == 1
    assert lines[0].text == "Prüfbericht"


@pytest.mark.parametrize(
    ("query", "is_regex", "text"),
    [
        ("PRÜFBERICHT", False, "Der Prüfbericht"),
        ("übergabeprotokoll", False, "Übergabeprotokoll unterschrieben"),
        (r"\bÄußerung\b", True, "Die Äußerung des Kunden"),
        (r"Pr\wfbericht", True, "Prüfbericht"),
    ],
)
def test_umlauts_fold_case_and_count_as_word_characters(query: str, is_regex: bool, text: str) -> None:
    assert _lines(KnowledgeContentPattern(query, is_regex=is_regex), text)[1] == 1


def test_case_sensitive_search_needs_the_same_case() -> None:
    assert _lines(KnowledgeContentPattern("rfc 9000", case_sensitive=True), "RFC 9000")[1] == 0


def test_anchors_mean_line_starts_and_crlf_lines_end_before_the_carriage_return() -> None:
    """`$` matches before `\\n` only, as in PCRE2's default and grep, so it does not match before a `\\r\\n`."""
    text = "Total: 5\r\nSubtotal: 4\r\nTotal: 9"
    lines, count = _lines(KnowledgeContentPattern(r"^Total: \d", is_regex=True), text)

    assert count == 2
    assert [line.text for line in lines] == ["Total: 5", "Total: 9"]


def test_a_match_across_lines_counts_for_the_line_it_starts_on() -> None:
    lines, count = _lines(KnowledgeContentPattern(r"RFC\s+9000", is_regex=True), "see RFC\n9000 here")

    assert count == 1
    assert (lines[0].line_number, lines[0].text) == (1, "see RFC")


def test_every_matching_line_is_counted_but_only_the_first_are_returned() -> None:
    text = "\n".join(f"line {index} Rechnung" for index in range(30))
    lines, count = _lines(KnowledgeContentPattern("rechnung"), text, max_lines_per_document=5)

    assert count == 30
    assert [line.line_number for line in lines] == [1, 2, 3, 4, 5]
