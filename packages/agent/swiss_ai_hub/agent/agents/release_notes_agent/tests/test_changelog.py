from unittest.mock import AsyncMock

import pytest

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_renderer import ChangelogRenderer
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_stream import ChangelogStream
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.agents.release_notes_agent.release_note import ReleaseNote
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

_T = AgentLocaleHandler("en")


def _note(key: str, section: ChangelogSection, note: str) -> ReleaseNote:
    project, number = key.split("-")
    return ReleaseNote(
        key=key,
        url=f"https://jira.example.com/browse/{key}",
        project=project,
        number=int(number),
        section=section,
        summary=f"Summary of {key}",
        note=note,
    )


@pytest.mark.parametrize(
    ("issue_type", "section"),
    [
        ("Bug", ChangelogSection.FIXES),
        ("  bug ", ChangelogSection.FIXES),
        ("Fehler", ChangelogSection.FIXES),
        ("Story", ChangelogSection.FEATURES),
        ("New Feature", ChangelogSection.FEATURES),
        ("Nouvelle fonctionnalité", ChangelogSection.FEATURES),
        ("Improvement", ChangelogSection.IMPROVEMENTS),
        ("Verbesserung", ChangelogSection.IMPROVEMENTS),
        ("Task", ChangelogSection.OTHER),
        ("Sub-task", ChangelogSection.OTHER),
        ("Epic", ChangelogSection.OTHER),
        (None, ChangelogSection.OTHER),
    ],
)
def test_issue_types_map_to_changelog_sections(issue_type: str | None, section: ChangelogSection):
    assert ChangelogSection.of_issue_type(issue_type) is section


def test_sections_rank_in_changelog_order():
    assert [section.rank for section in ChangelogSection] == [0, 1, 2, 3]
    assert list(ChangelogSection) == [
        ChangelogSection.FEATURES,
        ChangelogSection.FIXES,
        ChangelogSection.IMPROVEMENTS,
        ChangelogSection.OTHER,
    ]


@pytest.mark.parametrize(
    ("language", "title", "fixes"),
    [
        (ReleaseLanguage.EN, "## Release notes 2.0\n", "\n### Fixes\n\n"),
        (ReleaseLanguage.DE, "## Versionshinweise 2.0\n", "\n### Fehlerbehebungen\n\n"),
        (ReleaseLanguage.FR, "## Notes de version 2.0\n", "\n### Corrections\n\n"),
        (ReleaseLanguage.IT, "## Note di rilascio 2.0\n", "\n### Correzioni\n\n"),
    ],
)
def test_titles_and_headings_are_in_the_block_language_whatever_the_run_locale(
    language: ReleaseLanguage, title: str, fixes: str
):
    assert ChangelogRenderer.title("2.0", language, _T) == title
    assert ChangelogRenderer.heading(ChangelogSection.FIXES, language, _T) == fixes


def test_every_section_has_a_heading_in_every_language():
    for language in ReleaseLanguage:
        headings = {ChangelogRenderer.heading(section, language, _T) for section in ChangelogSection}
        assert len(headings) == len(ChangelogSection)
        assert not any("release_notes_agent" in heading for heading in headings)


def test_a_bullet_leads_with_the_linked_key_only_when_asked_to():
    note = _note("ENG-12", ChangelogSection.FIXES, "Sign-in works\nagain  after a  timeout.")

    assert ChangelogRenderer.bullet(note, show_ticket_keys=True) == (
        "- [ENG-12](https://jira.example.com/browse/ENG-12): Sign-in works again after a timeout.\n"
    )
    assert ChangelogRenderer.bullet(note, show_ticket_keys=False) == "- Sign-in works again after a timeout.\n"


@pytest.mark.asyncio
async def test_the_stream_keeps_exactly_the_text_it_shows():
    displayer = AsyncMock()
    stream = ChangelogStream(displayer, _T, show_ticket_keys=False, model_name="gemma")

    await stream.begin(ReleaseLanguage.EN, "2.0")
    await stream.add([_note("ENG-1", ChangelogSection.FEATURES, "Export to CSV.")])
    await stream.add(
        [_note("ENG-2", ChangelogSection.FEATURES, "Dark mode."), _note("ENG-3", ChangelogSection.FIXES, "No crash.")]
    )
    await stream.begin(ReleaseLanguage.DE, "2.0")
    await stream.add([_note("ENG-1", ChangelogSection.FEATURES, "Export nach CSV.")])

    shown = [call.args[0] for call in displayer.display_chunk.await_args_list]
    assert stream.text == "".join(shown)
    assert stream.text == (
        "## Release notes 2.0\n"
        "\n### New features\n\n- Export to CSV.\n"
        "- Dark mode.\n\n### Fixes\n\n- No crash.\n"
        "\n## Versionshinweise 2.0\n"
        "\n### Neue Funktionen\n\n- Export nach CSV.\n"
    )
    assert {call.kwargs["model_name"] for call in displayer.display_chunk.await_args_list} == {"gemma"}


@pytest.mark.asyncio
async def test_the_stream_shows_nothing_for_an_empty_batch():
    displayer = AsyncMock()
    stream = ChangelogStream(displayer, _T, show_ticket_keys=True, model_name="gemma")

    await stream.add([])

    displayer.display_chunk.assert_not_awaited()
    assert stream.text == ""
