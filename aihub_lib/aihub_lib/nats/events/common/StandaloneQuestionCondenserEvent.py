from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class StandaloneQuestionCondenserEvent(ControlAndDisplayEvent):
    """
    Event to condense chat messages into a single standalone question as a chat message.
    """

    condensed_chat_message: ChatMessage = Field(
        ..., description="Single chat message containing the condensed user question."
    )
