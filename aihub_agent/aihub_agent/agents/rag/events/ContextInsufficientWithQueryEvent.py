from typing import Optional, List

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_agent.agents.rag.events.ContextInsufficientEvent import ContextInsufficientEvent


class ContextInsufficientWithQueryEvent(ContextInsufficientEvent):
    new_query: Optional[str] = Field(
        default=None, description="The new query to retrieve better context, if max_hops has not been exceeded."
    )
    history: Optional[List[ChatMessage]] = Field(default=None, description="The history of messages to retrieve.")
