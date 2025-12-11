from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.utils.limit_chat_history_with_context import limit_chat_history_with_context
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.rag.events import LimitChatHistoryWithContextEvent


def execute_limit_chat_history_with_context(
    chat_history: list[ChatMessage],
    context_message: ChatMessage,
    last_user_message: ChatMessage | None,
    llm_config: LLMConfig,
    number_of_input_tokens: int,
) -> LimitChatHistoryWithContextEvent:
    """
    Includes the combined context and truncates chat history again.
    """
    system_messages = [msg for msg in chat_history if msg.role == MessageRole.SYSTEM]
    limited_chat_history = limit_chat_history_with_context(
        chat_history=chat_history,
        context_messages=[context_message],
        system_messages=system_messages,
        last_user_message=last_user_message or ChatMessage(role=MessageRole.USER, content=""),
        tokenizer=llm_config.token_counter,
        number_of_input_tokens=number_of_input_tokens,
    )
    return LimitChatHistoryWithContextEvent(limited_history_with_context=limited_chat_history)
