from typing import List

from llama_index.core.base.llms.types import ChatMessage

from aihub_lib.nats.events import ControlEvent


class FewShotEvent(ControlEvent):
    few_shot_examples: List[ChatMessage]
    few_shot_system_prompt: ChatMessage | None
