from llama_index.core.base.llms.types import ChatMessage, MessageRole


def format_expert_conversation(conversation: list[ChatMessage]) -> str:
    """Format an expert conversation as a text string for context."""
    conversation_parts = []
    for msg in conversation:
        role_label = "Agent" if msg.role == MessageRole.ASSISTANT else "Expert"
        content = msg.content or ""
        conversation_parts.append(f"{role_label}: {content}")
    return "\n".join(conversation_parts)
