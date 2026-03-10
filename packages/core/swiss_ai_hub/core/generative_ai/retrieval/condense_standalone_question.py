from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM

from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler


def _messages_to_history_str(messages: list[ChatMessage]) -> str:
    """Convert messages to a history string."""
    string_messages = []
    for message in messages:
        role = message.role
        content = message.content
        string_message = f"{role.value}: {content}"

        additional_kwargs = message.additional_kwargs
        if additional_kwargs:
            string_message += f"\n{additional_kwargs}"
        string_messages.append(string_message)
    return "\n".join(string_messages)


def condense_standalone_question(
    message: ChatMessage,
    chat_history: list[ChatMessage],
    t: LocaleHandler,
    llm: LLM,
) -> ChatMessage:
    """
    Condenses a follow-up user question into a standalone question using chat history and a language model.

    This function takes a user message (as a ChatMessage, which may include text and multimodal content such as
    images) and reformulates it into a self-contained question that can be understood without the conversation
    history. The chat history provides context for resolving references and pronouns in the user's message.
    System messages are filtered out from the chat history before processing.
    """
    chat_history_without_system_messages = [msg for msg in chat_history if msg.role != MessageRole.SYSTEM]
    chat_history_str = _messages_to_history_str(chat_history_without_system_messages)

    prompt_template = PromptTemplate(t("lib.prompt.condenser.standalone_question"))
    instruction_content = prompt_template.format(chat_history=chat_history_str)
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=instruction_content), message]
    response = llm.chat(messages=messages)

    return ChatMessage(role=MessageRole.USER, content=response.message.content)
