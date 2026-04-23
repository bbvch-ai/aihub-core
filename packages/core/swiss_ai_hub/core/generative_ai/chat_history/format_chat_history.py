from llama_index.core.base.llms.types import ChatMessage


def format_chat_history(chat_history: list[ChatMessage]) -> str:
    """Serialize chat messages as ``role: content`` lines for inclusion in prompt templates.

    Messages with empty content (e.g. tool-call placeholders) are skipped so the resulting
    block stays compact.
    """
    return "\n".join(f"{message.role.value}: {message.content}" for message in chat_history if message.content)
