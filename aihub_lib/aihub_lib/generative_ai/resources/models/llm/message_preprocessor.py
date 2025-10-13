from llama_index.core.base.llms.types import ChatMessage


def merge_consecutive_messages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Merge consecutive messages with the same role."""
    if not messages:
        return messages

    merged = [messages[0]]

    for message in messages[1:]:
        if message.role == merged[-1].role:
            merged_content = f"{merged[-1].content}\n\n{message.content}"
            merged[-1] = ChatMessage(role=message.role, content=merged_content)
        else:
            merged.append(message)

    return merged
