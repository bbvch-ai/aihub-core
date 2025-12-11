from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.nats.events import LimitChatHistoryEvent
from llama_index.core.base.llms.types import ChatMessage


def execute_limit_chat_history(
    messages: list[ChatMessage],
    number_of_input_tokens: int,
) -> LimitChatHistoryEvent:
    """
    Truncates incoming chat messages to fit within the configured token limit.
    """
    limited_chat_history = limit_chat_history(
        chat_history=messages,
        number_of_input_tokens=number_of_input_tokens,
    )
    return LimitChatHistoryEvent(limited_history=limited_chat_history)
