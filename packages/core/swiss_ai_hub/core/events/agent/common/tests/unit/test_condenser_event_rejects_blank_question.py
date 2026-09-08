"""The condenser event itself refuses a blank question.

The condenser raises on the live path, but events are also deserialized on JetStream replay and
redelivery, where no step body runs. Validating on the field is what covers those paths — and a length
constraint cannot express it, because the field is a llama-index `ChatMessage` and the check has to reach
`.content`.
"""

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError

from swiss_ai_hub.core.events.agent.common.standalone_question_condenser_event import (
    StandaloneQuestionCondenserEvent,
)


@pytest.mark.parametrize("content", [None, "", "   ", "\n"], ids=["none", "empty", "spaces", "newline"])
def test_blank_content_is_rejected(content):
    with pytest.raises(ValidationError):
        StandaloneQuestionCondenserEvent(condensed_chat_message=ChatMessage(role=MessageRole.USER, content=content))


def test_a_real_question_is_accepted_and_exposed_by_the_accessor():
    event = StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="Do we offer a part-time discount?")
    )

    assert event.condensed_question == "Do we offer a part-time discount?"


def test_replay_of_a_blank_persisted_event_is_rejected():
    """The reason this lives on the field: deserialization is the path a step-level check cannot see."""
    payload = StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="a real question")
    ).model_dump()
    payload["condensed_chat_message"]["blocks"] = [{"block_type": "text", "text": "   "}]

    with pytest.raises(ValidationError):
        StandaloneQuestionCondenserEvent.model_validate(payload)
