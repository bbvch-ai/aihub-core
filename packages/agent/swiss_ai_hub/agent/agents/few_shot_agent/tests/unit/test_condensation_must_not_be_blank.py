"""FewShotAgent inherits the condenser guard, and must still read the blanks already on its stream.

`create_few_shot_examples` deliberately drops the chat history and the original user message from the final
prompt — the docstring says so — which makes the condensed question the sole carrier of what was asked. A
blank one is therefore worse here than in the RAG agents, not milder: the provider rejects the turn, or the
model classifies a question that was never posed.

The raise arrives for free from the shared core function, and that is the only place the invariant can act.
A `field_validator` on the event would run on JetStream replay too, where it can reject nothing but history
— see `test_condenser_event_reads_historical_blanks.py` in core.
"""

from unittest.mock import AsyncMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.generative_ai import EmptyCondensationError
from swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question import condense_standalone_question
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_standalone_question_condenser_event import (
    FewShotStandaloneQuestionCondenserEvent,
)


def test_a_real_question_is_accepted_and_exposed_by_the_accessor():
    event = FewShotStandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="Is a part-timer eligible?")
    )

    assert event.condensed_question == "Is a part-timer eligible?"


def test_a_blank_event_from_the_log_still_deserializes():
    payload = FewShotStandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="Is a part-timer eligible?")
    ).model_dump()
    payload["condensed_chat_message"]["blocks"] = []

    replayed = BaseEvent.deserialize_event(payload)

    assert isinstance(replayed, FewShotStandaloneQuestionCondenserEvent)
    assert replayed.condensed_question == ""


@pytest.mark.asyncio
async def test_the_shared_condenser_raises_before_the_event_is_built():
    """The step never reaches its own event construction — the core function is the only line of defence."""
    llm = AsyncMock()
    llm.achat.return_value = ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=""))

    with pytest.raises(EmptyCondensationError):
        await condense_standalone_question(
            message=ChatMessage(role=MessageRole.USER, content="what about part-timers?"),
            chat_history=[],
            t=LocaleHandler(),
            llm=llm,
        )
