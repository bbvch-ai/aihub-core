from jinja2 import Template
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.types.Memory import Memory
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation


def extend_chat_history_with_memory(
    chat_history: list[ChatMessage],
    memories: list[Memory],
    relations: list[MemoryRelation] | None,
    t: LocaleHandler,
) -> list[ChatMessage]:
    """
    Inserts retrieved memories as a system message after existing system messages to guide LLM responses.

    Why system message? LLMs treat system messages as authoritative background information that influences
    all subsequent responses without being part of the conversation flow. This ensures the model considers
    memories without confusing them with actual user/assistant dialogue. The function formats both individual
    memories and their relations to provide the LLM with knowledge graph context.

    Why after existing system messages? Agent behavior/personality system messages should come first to establish
    the foundational context, with user-specific memory context layered on top. This ensures agent configuration
    takes precedence while still providing personalized memory context.

    Why locale-specific prompts? Memory context should be presented in the user's preferred language to ensure
    clarity and natural integration with the conversation. Jinja2 templates enable conditional formatting
    (showing relations only if present) and consistent structure across all supported languages.
    """
    if not memories:
        return chat_history

    template_string = t("lib.prompt.memory.system_message")
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
