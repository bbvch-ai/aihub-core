"""The condenser refuses to return a blank standalone question.

Every caller treats the condensed question as the turn's only carrier of intent: it is embedded for document
and memory retrieval, stored as the user half of a mem0 turn, and posted to a human by `ExpertRAGAgent`.
`FewShotAgent` drops the chat history and the original message from its final prompt entirely, so a blank
one leaves the model classifying nothing.

Observed in production — 8 runs between 30 June and 14 July 2026, all `ExpertRAGAgent` — so this is a
guard against something that happens, not a hypothetical.
"""

from unittest.mock import AsyncMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole

from swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question import condense_standalone_question
from swiss_ai_hub.core.generative_ai.retrieval.empty_condensation_error import EmptyCondensationError
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


def _llm_returning(content: str | None) -> AsyncMock:
    llm = AsyncMock()
    llm.achat.return_value = ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=content))
    return llm


async def _condense(llm: AsyncMock) -> ChatMessage:
    return await condense_standalone_question(
        message=ChatMessage(role=MessageRole.USER, content="what about part-timers?"),
        chat_history=[ChatMessage(role=MessageRole.USER, content="Do we offer a discount?")],
        t=LocaleHandler(),
        llm=llm,
    )


@pytest.mark.parametrize("content", [None, "", "   ", "\n\t "], ids=["none", "empty", "spaces", "whitespace"])
@pytest.mark.asyncio
async def test_blank_condensation_raises(content):
    with pytest.raises(EmptyCondensationError):
        await _condense(_llm_returning(content))


@pytest.mark.asyncio
async def test_a_usable_condensation_is_returned_as_a_user_message():
    message = await _condense(_llm_returning("Do we offer a discount for part-time employees?"))

    assert message.role == MessageRole.USER
    assert message.content == "Do we offer a discount for part-time employees?"


@pytest.mark.asyncio
async def test_surrounding_whitespace_is_stripped():
    """Stripped rather than passed through: this string is embedded, and the callers compare it as a query."""
    message = await _condense(_llm_returning("  Do we offer a part-time discount?\n"))

    assert message.content == "Do we offer a part-time discount?"


@pytest.mark.asyncio
async def test_the_call_is_not_retried():
    """No retry by design — at temperature 0.1 an identical re-issue returns the same nothing."""
    llm = _llm_returning("")

    with pytest.raises(EmptyCondensationError):
        await _condense(llm)

    assert llm.achat.await_count == 1
