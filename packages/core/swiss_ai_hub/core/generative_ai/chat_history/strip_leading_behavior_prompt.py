from llama_index.core.base.llms.types import ChatMessage, MessageRole


def strip_leading_behavior_prompt(chat_history: list[ChatMessage]) -> list[ChatMessage]:
    """Drop the first message when it is a system message — in the RAG flow that slot
    holds the agent behavior prompt, which is irrelevant to the guard's sufficiency decision."""
    if chat_history and chat_history[0].role == MessageRole.SYSTEM:
        return chat_history[1:]
    return chat_history
