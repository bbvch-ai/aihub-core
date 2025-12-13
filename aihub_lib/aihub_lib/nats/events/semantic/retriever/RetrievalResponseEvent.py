from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.nats.events.control.stop import StopEvent
from aihub_lib.nats.events.semantic.retriever.RetrieverEvent import RetrieverEvent


class RetrievalResponseEvent(StopEvent, RetrieverEvent):
    """
    Unified response event from ANY retrieval agent.

    All retrieval agents return the same structure - context message, nodes, agent identification,
    and retrieval type. The orchestrator (RAGAgent) doesn't need to know what type of retrieval
    was performed.

    The `nodes` field is inherited from RetrieverEvent and contains the raw retrieved nodes
    with their scores and content.
    """

    context_message: Annotated[ChatMessage, Field(description="The ordered nodes as a context message.")]
    agent_id: Annotated[str, Field(description="The agent ID that produced these results.")]
    retrieval_type: Annotated[
        str, Field(description="The type of retrieval performed (knowledge, insight, sql, etc.).")
    ]
