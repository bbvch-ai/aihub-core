from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM

from swiss_ai_hub.core.generative_ai.retrieval.empty_condensation_error import EmptyCondensationError
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


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


async def condense_standalone_question(
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

    Uses ``achat`` (not ``chat``): a synchronous LLM call inside the agent's async event loop blocks every
    other coroutine for the whole request — on a reasoning model that is ~25s during which no other step,
    fan-out, or concurrent run can make progress.

    Raises `EmptyCondensationError` on a blank answer instead of returning one. This has been observed in
    production — 8 runs between 30 June and 14 July 2026 — and every caller treats the result as the turn's
    only question: it is embedded for retrieval and memory search, stored as the user half of a mem0 turn,
    and posted to a human by `ExpertRAGAgent`. There is no retry, because the callers run this at
    `temperature=0.1` and re-issuing an identical request that returned nothing does not return something
    (the same lesson as ADR `2026_07_13_response_format_as_default_structured_output`); transport failures
    are already retried below this layer.
    """
    chat_history_without_system_messages = [msg for msg in chat_history if msg.role != MessageRole.SYSTEM]
    chat_history_str = _messages_to_history_str(chat_history_without_system_messages)

    prompt_template = PromptTemplate(t("lib.prompt.condenser.standalone_question"))
    instruction_content = prompt_template.format(chat_history=chat_history_str)
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=instruction_content), message]
    response = await llm.achat(messages=messages)

    condensed = (response.message.content or "").strip()
    if not condensed:
        raise EmptyCondensationError(
            "The condenser returned no standalone question, so this turn has no usable query to retrieve, "
            "remember or escalate with."
        )

    return ChatMessage(role=MessageRole.USER, content=condensed)
