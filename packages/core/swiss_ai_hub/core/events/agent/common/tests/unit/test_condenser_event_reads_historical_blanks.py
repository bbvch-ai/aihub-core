"""The condenser event must stay deserializable, including the blanks written before the producer raised.

A `field_validator` on this field looked like the way to cover JetStream replay and redelivery, where no
step body runs. It is the opposite: the only events it can ever reject are the ones already in the log,
written by a version that predates `EmptyCondensationError` — replay then drops them on every agent start,
and `EventService.get_events_in_thread` fails the whole thread when the UI opens it. The invariant belongs
where it can still change the outcome, in `condense_standalone_question`.
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.events.agent.common.standalone_question_condenser_event import (
    StandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.core.events.base_event import BaseEvent


def test_a_real_question_survives_a_serialization_round_trip():
    event = StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="Do we offer a part-time discount?")
    )

    replayed = BaseEvent.deserialize_event(event.model_dump_json())

    assert isinstance(replayed, StandaloneQuestionCondenserEvent)
    assert replayed.condensed_question == "Do we offer a part-time discount?"


def test_a_blank_event_from_the_log_still_deserializes():
    """Shaped like the events observed on the stream: a `ChatMessage` that serialized with no blocks."""
    payload = StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="a real question")
    ).model_dump()
    payload["condensed_chat_message"]["blocks"] = []

    replayed = BaseEvent.deserialize_event(payload)

    assert isinstance(replayed, StandaloneQuestionCondenserEvent)
    assert replayed.condensed_question == ""
