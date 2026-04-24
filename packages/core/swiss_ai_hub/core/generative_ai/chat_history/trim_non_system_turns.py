from llama_index.core.base.llms.types import ChatMessage, MessageRole


def trim_non_system_turns(chat_history: list[ChatMessage], max_non_system_messages: int) -> list[ChatMessage]:
    """Keep all SYSTEM messages (memory) in place, keep only the last
    ``max_non_system_messages`` user/assistant messages, and preserve original order."""
    non_system_count = sum(1 for message in chat_history if message.role != MessageRole.SYSTEM)
    if non_system_count <= max_non_system_messages:
        return chat_history
    drop_count = non_system_count - max_non_system_messages
    trimmed: list[ChatMessage] = []
    for message in chat_history:
        if message.role != MessageRole.SYSTEM and drop_count > 0:
            drop_count -= 1
            continue
        trimmed.append(message)
    return trimmed
