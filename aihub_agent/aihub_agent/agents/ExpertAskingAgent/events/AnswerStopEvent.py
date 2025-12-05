from typing import Annotated

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.nats.events import StopEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class AnswerStopEvent(StopEvent):
    """Event representing the conclusion of an expert's response to a user's question."""

    expert_answer: Annotated[str, Field(..., description="The answer to the question")]
    chat_history: Annotated[
        list[ChatMessage],
        Field(description="The chat history between the agent and the expert"),
    ] = []
    nodes: Annotated[
        list[IngestedNode],
        Field(description="The nodes that were used to formulate the expert question"),
    ] = []
