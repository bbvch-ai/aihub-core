from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class ContextualizeConversationEvent(ControlEvent):
    """
    Asks the conversation capability to turn a limited chat history into a contextualized turn: inspect the
    message for a meta question, derive the query the turn is answered for, and title the thread.

    Built with `Conversation.contextualize(...)`; answered with `ConversationContextualizedEvent`, or with a
    stop event when the message was a meta question or could not be condensed.
    """

    history: Annotated[list[ChatMessage], Field(description="The chat history, already limited to the budget.")]
    user_query: Annotated[
        str | None,
        Field(
            description="The raw text of the user's message, inspected for a meta question. None for a "
            "programmatic start, which skips inspection."
        ),
    ] = None
