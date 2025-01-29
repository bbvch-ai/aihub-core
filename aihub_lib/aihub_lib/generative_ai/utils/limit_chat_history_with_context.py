from typing import Callable, List

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.utilities.token_counting import TokenCounter


def limit_chat_history_with_context(
    chat_history: List[ChatMessage],
    system_messages: List[ChatMessage],
    context_messages: List[ChatMessage],
    last_user_message: ChatMessage,
    tokenizer: Callable[[str], List[int]],
    number_of_input_tokens: int,
) -> List[ChatMessage]:
    minimum_tokens = TokenCounter(tokenizer).estimate_tokens_in_messages(
        [*system_messages, *context_messages, last_user_message]
    )

    if minimum_tokens >= number_of_input_tokens:
        raise ValueError(
            f"Tokens for system prompt, context and user prompt exceed the maximum number of input tokens: "
            f"{minimum_tokens} >= {number_of_input_tokens}"
        )

    chat_history_without_system_messages = [message for message in chat_history if message.role != MessageRole.SYSTEM]

    memory = ChatMemoryBuffer.from_defaults(
        chat_history=chat_history_without_system_messages[:-1],
        token_limit=number_of_input_tokens - minimum_tokens,
    )
    limited_history = memory.get()

    return [
        *system_messages,
        *context_messages,
        *limited_history,
        last_user_message,
    ]
