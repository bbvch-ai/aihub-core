from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.nats.events import StopEvent


class AnswerStopEvent(StopEvent):
    """Event representing the conclusion of an expert's response to a user's question."""

    expert_answer: Annotated[str, Field(..., description="The final answer to the question")]
    expert_conversation: Annotated[
        list[ChatMessage],
        Field(default_factory=list, description="The full conversation history with the expert"),
    ]
