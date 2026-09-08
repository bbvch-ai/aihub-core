"""FewShotAgent inherits the condenser guard, and needs its own event validator.

`create_few_shot_examples` deliberately drops the chat history and the original user message from the final
prompt — the docstring says so — which makes the condensed question the sole carrier of what was asked. A
blank one is therefore worse here than in the RAG agents, not milder: the provider rejects the turn, or the
model classifies a question that was never posed.

The raise arrives for free from the shared core function. The event validator does not: this event has a
different base (`ControlEvent`) from `StandaloneQuestionCondenserEvent` (`ControlAndDisplayEvent`), so there
is no shared ancestor to hang one validator on.
"""

from unittest.mock import AsyncMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.generative_ai import EmptyCondensationError
from swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question import condense_standalone_question
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_standalone_question_condenser_event import (
    FewShotStandaloneQuestionCondenserEvent,
)


@pytest.mark.parametrize("content", [None, "", "  "], ids=["none", "empty", "spaces"])
def test_the_event_rejects_a_blank_question(content):
    with pytest.raises(ValidationError):
        FewShotStandaloneQuestionCondenserEvent(
            condensed_chat_message=ChatMessage(role=MessageRole.USER, content=content)
        )


def test_a_real_question_is_accepted_and_exposed_by_the_accessor():
    event = FewShotStandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="Is a part-timer eligible?")
    )

    assert event.condensed_question == "Is a part-timer eligible?"


@pytest.mark.asyncio
async def test_the_shared_condenser_raises_before_the_event_is_built():
    """The step never reaches its own event construction — the core function is the first line of defence."""
    llm = AsyncMock()
    llm.achat.return_value = ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=""))

    with pytest.raises(EmptyCondensationError):
        await condense_standalone_question(
            message=ChatMessage(role=MessageRole.USER, content="what about part-timers?"),
            chat_history=[],
            t=LocaleHandler(),
            llm=llm,
        )
