from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class InOrderNodeCombinerEvent(ControlEvent):
    """
    An event that combines multiple nodes in order and transforms them to a context chat message.
    """
    context_message: ChatMessage = Field(..., description="The context message.")
