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
        ("Französisch bitte", [ReleaseLanguage.FR]),
    ],
)
def test_a_message_names_languages_in_any_platform_language(message: str, languages: list[ReleaseLanguage]):
    assert ReleaseLanguage.named_in(message) == languages


@pytest.mark.parametrize("message", ["release notes for 2.0", "our customers in Germany", "the englishman's ticket"])
def test_only_a_language_named_as_a_whole_word_counts(message: str):
    assert ReleaseLanguage.named_in(message) == []
