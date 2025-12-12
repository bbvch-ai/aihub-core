from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.schema import NodeWithScore
from pydantic import Field


class CombinedRetrievalEvent(ControlEvent):
    """
    Event containing combined results from all retrieval agents.

    Holds the aggregated context from knowledge retrieval agents and insight sources,
    along with metadata about which sources contributed to the results.
    """

    context_message: Annotated[
        ChatMessage, Field(description="The combined context message from all retrieval sources.")
    ]
    nodes: Annotated[list[NodeWithScore], Field(description="All retrieved nodes combined from all sources.")]
    knowledge_agent_ids: Annotated[
        list[str], Field(description="List of knowledge retrieval agent IDs that contributed to the results.")
    ]
    has_insights: Annotated[bool, Field(description="Whether insights were retrieved and included in the results.")]
