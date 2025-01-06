from typing import List

from aihub_lib.nats.events.semantic import SemanticEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryEvent(SemanticEvent):
    limited_history: List[ChatMessage]
