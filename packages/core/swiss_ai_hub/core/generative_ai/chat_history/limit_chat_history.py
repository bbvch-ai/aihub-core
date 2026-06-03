from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer


def _carries_content(message: ChatMessage) -> bool:
    """
    True if the message has something to send to the LLM: non-blank text, or a non-text block
    (image/audio). Empty-content turns must be dropped — a chat client can capture a streamed answer
    as an empty assistant message, and most providers reject an empty assistant message with a 400.
    """
    if str(message.content or "").strip():
        return True
    return any(getattr(block, "block_type", "text") != "text" for block in getattr(message, "blocks", []))


def limit_chat_history(number_of_input_tokens: int, chat_history: list[ChatMessage]) -> list[ChatMessage]:
    memory = ChatMemoryBuffer.from_defaults(
        chat_history=[message for message in chat_history if _carries_content(message)],
        token_limit=number_of_input_tokens,
    )
    return memory.get()
