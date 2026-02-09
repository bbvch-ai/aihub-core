from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class FewShotEvent(ControlEvent):
    few_shot_examples: list[ChatMessage]
    system_prompt: ChatMessage | None
    full_context: list[ChatMessage]
