"""
Shared step functions for RAG-based agents.

These functions extract reusable logic from RAG agent steps.
"""

from aihub_lib.generative_ai.resources.models.llm.message_preprocessor import merge_consecutive_messages
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StandaloneQuestionCondenserEvent
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ExpertRejectEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.schema import NodeWithScore

from aihub_agent.agents.RagAgent.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent


def get_query_from_event(event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent) -> str:
    """
    Extract query string from a condenser or insufficient context event.

    Args:
        event: Either a StandaloneQuestionCondenserEvent or ContextInsufficientWithQueryEvent

    Returns:
        The query string to use for retrieval
    """
    if isinstance(event, StandaloneQuestionCondenserEvent):
        return event.condensed_chat_message.content or ""
    return event.new_query


def get_nodes_from_event(event: RetrieverEvent | RerankerEvent) -> list[NodeWithScore]:
    """
    Extract nodes from a retriever or reranker event.

    Args:
        event: Either a RetrieverEvent or RerankerEvent

    Returns:
        List of nodes with scores
    """
    if isinstance(event, RerankerEvent):
        return event.output_nodes
    return event.nodes


def format_expert_conversation(conversation: list[ChatMessage]) -> str:
    """
    Format an expert conversation as a text string for context.

    Args:
        conversation: List of chat messages from expert conversation

    Returns:
        Formatted conversation text with Agent:/Expert: labels
    """
    conversation_parts = []
    for msg in conversation:
        role_label = "Agent" if msg.role == MessageRole.ASSISTANT else "Expert"
        content = msg.content or ""
        conversation_parts.append(f"{role_label}: {content}")
    return "\n".join(conversation_parts)


def build_llm_response_messages(
    event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent,
    limited_history_without_context: list[ChatMessage],
    context_insufficient_prompt: LocaleString | None,
    system_prompt: LocaleString | None,
    t: LocaleHandler,
) -> list[ChatMessage]:
    """
    Build the messages list for LLM response generation.

    Handles both normal responses (with context) and reject responses (few-shot, context insufficient, expert reject).

    Args:
        event: The event containing response data or rejection info
        limited_history_without_context: Chat history without context (for reject responses)
        context_insufficient_prompt: Prompt for context insufficient cases
        system_prompt: Optional system prompt
        t: Locale handler for translations

    Returns:
        List of ChatMessages ready for LLM
    """
    if isinstance(event, FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent):
        context_insufficient_prompt_text = t.extract(context_insufficient_prompt)
        prompt_text = t("agent.prompt.guard.reject").format(
            prompt=context_insufficient_prompt_text, reason=event.reason
        )
        messages = limited_history_without_context + [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=prompt_text,
            ),
        ]
    else:
        messages = event.limited_history_with_context

    system_prompt_text = t.extract(system_prompt) if system_prompt else None
    if system_prompt_text:
        system_message = ChatMessage(role=MessageRole.SYSTEM, content=system_prompt_text)
        messages = [system_message] + messages

    # Merge consecutive messages with the same role (required by LiteLLM)
    return merge_consecutive_messages(messages)
