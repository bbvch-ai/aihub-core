"""The condenser is told which files this message attached, so a demonstrative resolves to them.

The chat client forwards every attachment of the thread on every turn, so the whole list says nothing about
what "this document" points at — only the subset the user attached to the message being answered does.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import UserUploadedFile
from swiss_ai_hub.core.i18n import LocaleHandler

import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.rag.step_functions import do_condense_standalone_question

_MODULE = "swiss_ai_hub.agent.rag.step_functions"
_FILE_ID = "bfdc8835-a20d-43f5-8f21-ff8140ad83d3"


def _file(filename: str, attached_in_current_turn: bool) -> UserUploadedFile:
    return UserUploadedFile(
        filename=filename,
        file_type="application/pdf",
        file_id=_FILE_ID,
        source_file_id=_FILE_ID,
        attached_in_current_turn=attached_in_current_turn,
    )


def _llm_config() -> MagicMock:
    llm_config = MagicMock()
    llm_config.cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
    llm_config.cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=False)
    return llm_config


async def _condense(files: list[UserUploadedFile] | None) -> list[str]:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    message = ChatMessage(role=MessageRole.USER, content="what is in this document?")

    with patch(f"{_MODULE}.condense_standalone_question", new=AsyncMock(return_value=message)) as condense:
        await do_condense_standalone_question(
            [], message, _llm_config(), displayer, LocaleHandler(), None, uploaded_files=files
        )

    return condense.call_args.kwargs["attached_filenames"]


@pytest.mark.asyncio
async def test_only_the_files_of_this_message_are_named():
    """A thread's carry-over would drown the one file the demonstrative actually means."""
    files = [_file("carried.pdf", False), _file("just-attached.pdf", True), _file("older.pdf", False)]

    assert await _condense(files) == ["just-attached.pdf"]


@pytest.mark.asyncio
async def test_a_turn_that_attached_nothing_names_nothing():
    """Then the reference really does belong to the history, which is the pre-existing behaviour."""
    assert await _condense([_file("carried.pdf", False)]) == []


@pytest.mark.asyncio
async def test_an_agent_reached_without_files_still_condenses():
    assert await _condense(None) == []
