from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.nats.events import ControlEvent


class FewShotEvent(ControlEvent):
    few_shot_examples: list[ChatMessage]
    system_prompt: ChatMessage | None
    full_context: list[ChatMessage]
