from jinja2 import Template
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.types.Memory import Memory
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation


def extend_chat_history_with_user_memory(
    chat_history: list[ChatMessage],
    memories: list[Memory],
    relations: list[MemoryRelation] | None,
    t: LocaleHandler,
) -> list[ChatMessage]:
    """
    Inserts retrieved user memories as a system message to provide personalized context.

    User memories are private facts learned from this specific user's past conversations with this agent.
    They provide personalization but should only be referenced when relevant to the current query.

    Why system message? LLMs treat system messages as authoritative background information that influences
    responses without being part of the conversation flow. User memories are presented as optional context
    that the LLM may or may not use based on relevance.

    Why after existing system messages? Agent behavior/personality system messages come first to establish
    foundational context, with user-specific memory context layered on top.
    """
    if not memories:
        return chat_history

    template_string = t("lib.prompt.memory.user_memory_system_message")
    template = Template(template_string)
    memory_content = template.render(memories=memories, relations=relations or [])
    memory_message = ChatMessage(role=MessageRole.SYSTEM, content=memory_content)

    # Find the index after the last system message at the start of chat history
    insert_index = 0
    for i, message in enumerate(chat_history):
        if message.role == MessageRole.SYSTEM:
            insert_index = i + 1
        else:
            break

    # Insert memory message after all existing system messages
    chat_history.insert(insert_index, memory_message)
    return chat_history
