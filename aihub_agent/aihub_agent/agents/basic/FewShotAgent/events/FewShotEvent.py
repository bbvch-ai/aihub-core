from typing import List

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class FewShotEvent(ControlEvent):
    few_shot_examples: List[ChatMessage]
    few_shot_system_prompt: ChatMessage | None
    full_context: List[ChatMessage]
