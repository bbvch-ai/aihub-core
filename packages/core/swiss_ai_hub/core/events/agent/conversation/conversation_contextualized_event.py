from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class ConversationContextualizedEvent(ControlEvent):
    """
    The answer to `ContextualizeConversationEvent`: the turn is a normal request, and this is the one query
    every capability and the blueprint answer it for.
    """

    history: Annotated[list[ChatMessage], Field(description="The limited chat history the request carried.")]
    query: Annotated[
        str,
        Field(description="The question this turn is answered for. Blank when the message carried no text."),
    ]
    condensed: Annotated[
        bool,
        Field(description="Whether the query was condensed from the history rather than taken verbatim."),
    ] = False

    @property
    def is_blank(self) -> bool:
        return not self.query.strip()
