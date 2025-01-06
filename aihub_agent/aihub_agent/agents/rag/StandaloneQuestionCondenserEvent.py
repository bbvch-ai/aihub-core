from aihub_lib.nats.events.semantic import SemanticEvent
from llama_index.core.base.llms.types import ChatMessage


class StandaloneQuestionCondenserEvent(SemanticEvent):
    condensed_chat_message: ChatMessage
