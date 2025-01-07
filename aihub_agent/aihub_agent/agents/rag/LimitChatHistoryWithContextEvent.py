from typing import List

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryWithContextEvent(ControlEvent):
    limited_history_with_context: List[ChatMessage]
