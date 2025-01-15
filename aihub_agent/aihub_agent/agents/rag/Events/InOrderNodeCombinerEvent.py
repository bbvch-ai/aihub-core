from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class InOrderNodeCombinerEvent(ControlEvent):
    """
    Event to combine chat messages in order.
    """
    context_message: ChatMessage
