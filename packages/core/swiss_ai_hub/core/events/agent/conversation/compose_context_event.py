from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class ComposeContextEvent(ControlEvent):
    """
    Asks the conversation capability to merge context blocks into a chat history, in the given order, behind
    the leading system messages and within the input budget.

    Built with `Conversation.compose(...)`; answered with `ContextComposedEvent`.
    """

    history: Annotated[list[ChatMessage], Field(description="The chat history to merge the blocks into.")]
    blocks: Annotated[
        list[list[ChatMessage]],
        Field(description="Context blocks in the order they should reach the model. Empty blocks are skipped."),
    ] = []
