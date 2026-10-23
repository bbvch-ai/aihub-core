from unittest.mock import AsyncMock

import pytest
from swiss_ai_hub.core.events.agent import LLMStopEvent
from swiss_ai_hub.core.jira import (
    JiraAuthenticationError,
    JiraConfigurationError,
    JiraError,
    JiraInvalidQueryError,
    JiraProjectNotFoundError,
    JiraRequestError,
    JiraTooManyTicketsError,
    JiraVersion,
)

from swiss_ai_hub.agent.agents.release_notes_agent.jira_error_reply import JiraErrorReply
from swiss_ai_hub.agent.agents.release_notes_agent.release_notes_reply import ReleaseNotesReply
from swiss_ai_hub.agent.agents.release_notes_agent.version_match import VersionMatch
from swiss_ai_hub.agent.agents.release_notes_agent.version_match_outcome import VersionMatchOutcome
from swiss_ai_hub.agent.agents.release_notes_agent.version_match_reply import VersionMatchReply
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

_T = AgentLocaleHandler("en")


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (JiraAuthenticationError("https://jira.example.com", 401), "rejected this assistant's credentials"),
        (JiraProjectNotFoundError("ENG", "Release Bot"), "Jira project ENG does not exist"),
        (JiraProjectNotFoundError("ENG", "Release Bot", renamed_to="PLAT"), "renamed to PLAT"),
        (JiraInvalidQueryError(["Field 'sprnt' does not exist"]), "rejected this assistant's JQL filter"),
        (JiraTooManyTicketsError(300, 412), "more than 300 tickets"),
        (JiraConfigurationError(["the API token is missing"]), "Jira connection is not set up correctly"),
        (JiraRequestError("Jira answered 500 to GET /rest/api/2/search", 500, "/rest/api/2/search", ""), "try again"),
        (JiraError("Jira at jira.example.com did not respond (ConnectTimeout)."), "try again"),
    ],
)
def test_each_jira_failure_is_one_sentence_and_keeps_jiras_words_as_detail(error: JiraError, expected: str):
    reply = JiraErrorReply.from_error(error, _T)

    assert expected in reply.message
    assert reply.detail == str(error)
    assert "agent.release_notes_agent" not in reply.message


def test_a_jira_failure_is_worded_in_the_run_language():
    reply = JiraErrorReply.from_error(JiraProjectNotFoundError("ENG", "Bot"), AgentLocaleHandler("de"))

    assert reply.message.startswith("Das Jira-Projekt ENG existiert nicht")
    assert "does not exist" in reply.detail


@pytest.mark.parametrize(
    ("match", "expected"),
    [
        (
            VersionMatch(outcome=VersionMatchOutcome.SEVERAL, names=["2.0", "1.0"]),
            "Your message names several releases: 2.0, 1.0.",
        ),
        (
            VersionMatch(outcome=VersionMatchOutcome.UNKNOWN, requested="2.4", suggestions=["2.4.0"], recent=["3.0"]),
            "I found no fix version 2.4 in ENG, SD. Did you mean: 2.4.0?",
        ),
        (
            VersionMatch(outcome=VersionMatchOutcome.UNKNOWN, requested="9.9", recent=["3.0", "2.0"]),
            "I found no fix version 9.9 in ENG, SD. Recent versions are: 3.0, 2.0.",
        ),
        (
            VersionMatch(outcome=VersionMatchOutcome.UNKNOWN, requested="9.9"),
            "I found no fix version 9.9 in ENG, SD; Jira lists no fix versions there yet.",
        ),
        (
            VersionMatch(outcome=VersionMatchOutcome.MISSING, recent=["3.0", "2.0"]),
            "Name a fix version, for example: 3.0, 2.0.",
        ),
        (
            VersionMatch(outcome=VersionMatchOutcome.MISSING),
            "Jira lists no fix versions in ENG, SD",
        ),
    ],
)
def test_an_unresolved_version_gets_a_reply_the_user_can_answer(match: VersionMatch, expected: str):
    assert expected in VersionMatchReply.message(match, ["ENG", "SD"], _T)


def test_a_found_version_needs_no_reply():
    found = VersionMatch(outcome=VersionMatchOutcome.FOUND, versions=[JiraVersion(id="1", name="2.0", project="ENG")])

    with pytest.raises(ValueError, match="2.0 was found"):
        VersionMatchReply.message(found, ["ENG"], _T)


def test_the_follow_ups_see_the_writing_language_and_the_run_ends_on_everything_shown():
    request = ReleaseNotesReply.complete(
        question="release notes for 2.0",
        shown="## Release notes 2.0\n- A\n\n## Versionshinweise 2.0\n- B\n",
        model_name="gemma",
        answered="## Release notes 2.0\n- A\n",
    )

    assert isinstance(request, Conversation.CompleteRequest)
    assert [(message.role, message.content) for message in request.answer.input_messages] == [
        ("user", "release notes for 2.0")
    ]
    assert request.answer.output_messages[0].content == "## Release notes 2.0\n- A\n"
    assert isinstance(request.stop, LLMStopEvent)
    assert request.stop.input_messages == request.answer.input_messages
    assert request.stop.output_messages[0].content == "## Release notes 2.0\n- A\n\n## Versionshinweise 2.0\n- B\n"
    assert request.stop.chat_model_name == "gemma"


@pytest.mark.asyncio
async def test_a_sentence_is_streamed_before_the_run_ends_on_it():
    displayer = AsyncMock()

    request = await ReleaseNotesReply.say("Which release?", "release notes", displayer, "ReleaseNotesAgent")

    displayer.display_chunk.assert_awaited_once_with("Which release?", model_name="ReleaseNotesAgent")
    assert request.answer.output_messages[0].content == "Which release?"
    assert request.stop.output_messages[0].content == "Which release?"
