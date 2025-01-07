from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class InOrderNodeCombinerEvent(ControlEvent):
    context_message: ChatMessage
