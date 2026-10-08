import unicodedata

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index_query import KnowledgeTextIndexQuery

pytestmark = pytest.mark.unit


def _patterns(query: str, case_sensitive: bool = False) -> list[str] | None:
    index_query = KnowledgeTextIndexQuery.from_query(query, is_regex=False, case_sensitive=case_sensitive)
    return None if index_query is None else index_query.patterns


def test_a_literal_becomes_a_substring_pattern() -> None:
    assert _patterns("Zeta Dynamics AG") == ["%Zeta Dynamics AG%"]


def test_a_regex_is_never_translated() -> None:
    assert KnowledgeTextIndexQuery.from_query("Zeta.*AG", is_regex=True, case_sensitive=False) is None


def test_like_wildcards_and_the_escape_character_are_escaped() -> None:
    assert _patterns(r"100% sicher_v2 C:\Daten") == [r"%100\% sicher\_v2 C:\\Daten%"]


def test_quotes_and_control_characters_stay_as_they_are() -> None:
    assert _patterns('Abschnitt "Haftung"\tSeite') == ['%Abschnitt "Haftung"\tSeite%']


def test_composed_and_decomposed_spellings_are_both_searched() -> None:
    assert _patterns("Prüfbericht") == ["%Prüfbericht%", f"%{unicodedata.normalize('NFD', 'Prüfbericht')}%"]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("5 µg Wirkstoff", "%5 _g Wirkstoff%"),
        ("5 μg Wirkstoff", "%5 _g Wirkstoff%"),
        ("ΟΔΟΣ Athen", "%ΟΔΟ_ Athen%"),
        ("Straße Strasse ſtraße", "%Straße Strasse _traße%"),
        ("INDEX index", "%INDEX index%"),
    ],
)
def test_letters_case_folding_treats_differently_become_wildcards_when_case_is_ignored(
    query: str, expected: str
) -> None:
    assert _patterns(query) == [expected]


def test_case_sensitive_queries_keep_every_letter() -> None:
    assert _patterns("5 µg Wirkstoff", case_sensitive=True) == ["%5 µg Wirkstoff%"]


@pytest.mark.parametrize(
    "query",
    [
        "ab",
        "a.b.c",
        "12 34",
        "µg/ml",
        "Käse",
    ],
)
def test_a_query_without_three_word_characters_in_a_row_scans(query: str) -> None:
    """`Käse` decomposes into `Ka`, a combining mark and `se`, so its decomposed spelling has no trigram."""
    assert _patterns(query) is None


def test_case_sensitivity_picks_the_operator() -> None:
    assert KnowledgeTextIndexQuery.from_query("Rechnung", is_regex=False, case_sensitive=True).case_sensitive
    assert not KnowledgeTextIndexQuery.from_query("Rechnung", is_regex=False, case_sensitive=False).case_sensitive
