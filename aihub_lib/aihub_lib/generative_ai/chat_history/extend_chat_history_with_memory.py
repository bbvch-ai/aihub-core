from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.infrastructure.mem0.types.Memory import Memory
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation


def extend_chat_history_with_memory(
    chat_history: list[ChatMessage], memories: list[Memory], relations: list[MemoryRelation] | None = None
) -> list[ChatMessage]:
    """
    Prepends retrieved memories as a system message to guide LLM responses with long-term context.

    Why system message? LLMs treat system messages as authoritative background information that influences
    all subsequent responses without being part of the conversation flow. This ensures the model considers
    memories without confusing them with actual user/assistant dialogue. The function formats both individual
    memories and their relations to provide the LLM with knowledge graph context.
    """
    memory_content = "--\nUSER MEMORIES:\n"
    for memory in memories:
        memory_content += f"- {memory.memory}\n"
    memory_content += "\nRELATIONS:\n"
    for relation in relations or []:
        memory_content += f"- {relation.source} -> {relation.relation} -> {relation.target}\n"
    memory_content += "---"
    chat_history = [ChatMessage(role=MessageRole.SYSTEM, content=memory_content), *chat_history]
    return chat_history
