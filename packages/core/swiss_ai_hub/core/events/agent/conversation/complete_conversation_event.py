from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_event import LLMEvent


class CompleteConversationEvent(ControlEvent):
    """
    Asks the conversation capability to end the turn: generate the follow-up questions from the answer, then
    emit the stop event.

    Built with `Conversation.complete(...)`. Anything that must be published before the run tears down, such
    as a memory-storage delegation, is returned from the same step ahead of this event.
    """

    answer: Annotated[LLMEvent, Field(description="The answer the follow-up questions are grounded on.")]
    stop: Annotated[
        StopEvent | None,
        Field(
            description="The stop event to end the run with. None ends it with an `LLMStopEvent` carrying the answer."
        ),
    ] = None
