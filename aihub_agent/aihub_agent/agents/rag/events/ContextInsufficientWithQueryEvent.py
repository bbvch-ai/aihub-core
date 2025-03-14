from typing import Optional

from pydantic import Field

from aihub_agent.agents.rag.events.ContextInsufficientEvent import ContextInsufficientEvent


class ContextInsufficientWithQueryEvent(ContextInsufficientEvent):
    new_query: Optional[str] = Field(
        default=None, description="The new query to retrieve better context, if max_hops has not been exceeded."
    )
