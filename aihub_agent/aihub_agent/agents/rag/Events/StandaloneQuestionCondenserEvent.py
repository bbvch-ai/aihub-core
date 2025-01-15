from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class StandaloneQuestionCondenserEvent(ControlEvent):
    """
    Event to condense a chat message into a standalone question.
    """
    condensed_chat_message: ChatMessage = Field(..., description="The condensed chat message.")
