from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer


def _carries_content(message: ChatMessage) -> bool:
    """
    True if the message has something to send to the LLM: non-blank text, or a non-text block
    (image/audio). Empty-content turns are dropped because most providers reject an empty assistant
    message with a 400. The blank-answer race that produced these is fixed at the source (#1443 drains
    display-event streams before teardown); this is now a backstop against any empty turn that still
    slips through (e.g. a cached conversation or a different chat client).
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
