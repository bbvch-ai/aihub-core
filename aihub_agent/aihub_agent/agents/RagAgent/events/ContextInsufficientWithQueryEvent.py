from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_agent.agents.RagAgent.events.ContextInsufficientEvent import ContextInsufficientEvent


class ContextInsufficientWithQueryEvent(ContextInsufficientEvent):
    new_query: Annotated[
        str | None, Field(description="The new query to retrieve better context, if max_hops has not been exceeded.")
    ] = None
    history: Annotated[list[ChatMessage] | None, Field(description="The history of messages to retrieve.")] = None
