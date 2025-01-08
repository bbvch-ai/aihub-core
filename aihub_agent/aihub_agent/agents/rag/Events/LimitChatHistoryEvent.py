from typing import List

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryEvent(ControlEvent):
    limited_history: List[ChatMessage]
