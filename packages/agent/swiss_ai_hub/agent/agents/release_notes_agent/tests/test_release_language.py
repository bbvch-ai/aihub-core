import pytest

from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage


@pytest.mark.parametrize(
    ("message", "languages"),
    [
        ("Release notes for 2.0 in French", [ReleaseLanguage.FR]),
        ("Versionshinweise 2.0 auf Deutsch und Englisch", [ReleaseLanguage.DE, ReleaseLanguage.EN]),
        ("notes de version 2.0 en français", [ReleaseLanguage.FR]),
        ("notes de version 2.0 en francais", [ReleaseLanguage.FR]),
        ("note di rilascio 2.0 in italiano", [ReleaseLanguage.IT]),
        ("in English and in GERMAN please", [ReleaseLanguage.EN, ReleaseLanguage.DE]),
        ("2.0 in German, German please", [ReleaseLanguage.DE]),
        ("Versionshinweise 2.0, übersetzt ins Englische", [ReleaseLanguage.EN]),
        ("Release notes 2.0, translated into Italian", [ReleaseLanguage.IT]),
        ("2.0 in English, German and French", [ReleaseLanguage.EN, ReleaseLanguage.DE, ReleaseLanguage.FR]),
        ("Versionshinweise 2.0 auf Deutsch und Italienisch", [ReleaseLanguage.DE, ReleaseLanguage.IT]),
    ],
)
def test_a_message_names_languages_in_any_platform_language(message: str, languages: list[ReleaseLanguage]):
    assert ReleaseLanguage.named_in(message) == languages


@pytest.mark.parametrize(
    "message",
    [
        "release notes for 2.0",
        "our customers in Germany",
        "the englishman's ticket",
        "Release Notes für 2.0 für unsere Kunden in Italien",
        "Release notes 2.0 for Deutsche Bahn",
        "Release notes 2.0 for English-speaking customers",
        "Release notes 2.0 for the French team",
        "German release notes for 2.0",
        "Versionshinweise 2.0 für alle in deutschen Filialen",
        "Französisch bitte",
    ],
)
def test_a_name_counts_only_after_the_word_that_asks_for_the_language(message: str):
    """Without that word a name is a country, a company or an adjective, and the profile's languages stay."""
    assert ReleaseLanguage.named_in(message) == []


def test_a_name_listed_after_a_requested_one_must_be_in_the_same_language():
    assert ReleaseLanguage.named_in("Versionshinweise 2.0 auf Deutsch und Italien") == [ReleaseLanguage.DE]
