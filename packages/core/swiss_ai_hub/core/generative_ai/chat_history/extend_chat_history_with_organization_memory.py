from jinja2 import Template
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_relation import MemoryRelation


def render_organization_memory_content(
    memories: list[Memory],
    relations: list[MemoryRelation] | None,
    t: LocaleHandler,
) -> str | None:
    """Render organization memories into a text block using the shared i18n template.

    Returns None when there is nothing to render. Used both to build the chat-history
    system message and to extend the context passed to the sufficiency guard so that
    previously-stored expert answers can satisfy the guard without re-escalation.
    """
    if not (memories or relations):
        return None

    template_string = t("lib.prompt.memory.organization_memory_system_message")
    template = Template(template_string)
    return template.render(memories=memories, relations=relations or [])


def extend_chat_history_with_organization_memory(
    chat_history: list[ChatMessage],
    memories: list[Memory],
    relations: list[MemoryRelation] | None,
    t: LocaleHandler,
) -> list[ChatMessage]:
    """
    Inserts retrieved organization memories as a system message to provide shared organizational context.

    Organization memories are explicit facts about the organization (policies, tech stack, processes)
    that are shared across all users. They provide organizational context but should only be referenced
    when relevant to the current query.

    Why system message? LLMs treat system messages as authoritative background information. Organization
    memories are presented as optional context that the LLM may or may not use based on relevance.

    Why after existing system messages? Agent behavior/personality system messages come first to establish
    foundational context, with organizational memory context layered on top.
    """
    memory_content = render_organization_memory_content(memories, relations, t)
    if memory_content is None:
        return chat_history

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
