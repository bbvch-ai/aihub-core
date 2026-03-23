from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer


def limit_chat_history(number_of_input_tokens: int, chat_history: list[ChatMessage]) -> list[ChatMessage]:
    memory = ChatMemoryBuffer.from_defaults(
        chat_history=chat_history,
        token_limit=number_of_input_tokens,
    )
    return memory.get()
