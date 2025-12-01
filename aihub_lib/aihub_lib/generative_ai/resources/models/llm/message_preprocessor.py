from llama_index.core.base.llms.types import ChatMessage, TextBlock


def merge_consecutive_messages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Merge consecutive messages with the same role."""
    if not messages:
        return messages

    merged = [messages[0]]

    for message in messages[1:]:
        if message.role == merged[-1].role:
            prev_blocks = merged[-1].blocks or []
            curr_blocks = message.blocks or []
            separator = [TextBlock(text="\n\n")] if prev_blocks and curr_blocks else []
            merged[-1] = ChatMessage(role=message.role, blocks=prev_blocks + separator + curr_blocks)
        else:
            merged.append(message)

    return merged
