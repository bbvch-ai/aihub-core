from typing import Annotated, List, Optional

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_agent.agents.RagAgent.events.ContextInsufficientEvent import ContextInsufficientEvent


class ContextInsufficientWithQueryEvent(ContextInsufficientEvent):
    new_query: Annotated[
        Optional[str], Field(description="The new query to retrieve better context, if max_hops has not been exceeded.")
    ] = None
    history: Annotated[Optional[List[ChatMessage]], Field(description="The history of messages to retrieve.")] = None
