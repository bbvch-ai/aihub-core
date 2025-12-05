from typing import Annotated, Literal

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.nats.events import StartEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class InsightStartEvent(StartEvent):
    """
    Event that starts the InsightAgent workflow.
    Contains the chat history and nodes from an expert conversation
    to extract and store insights for future retrieval.
    """

    chat_history: Annotated[
        list[ChatMessage],
        Field(description="The chat history between the agent and the expert"),
    ]
    nodes: Annotated[
        list[IngestedNode],
        Field(description="The nodes that were used to formulate the expert question"),
    ]
    question: Annotated[str, Field(description="The original question that was asked")]
    expert_answer: Annotated[str, Field(description="The answer provided by the expert")]
    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language of the user.")] = "en"
