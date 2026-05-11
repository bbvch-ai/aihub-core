from swiss_ai_hub.core.events.agent import (
    AddMemoryToChatHistoryEvent,
    AgentInTheLoop,
    ContextSufficientAcceptEvent,
    RerankerEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieverEvent,
    RetrieveUserMemoryEvent,
    StoreUserMemoryEvent,
)

from swiss_ai_hub.agent.agents.expert_asking_agent.events.answer_stop_event import AnswerStopEvent
from swiss_ai_hub.agent.agents.expert_asking_agent.events.no_answer_stop_event import NoAnswerStopEvent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent


def check_reranking_enabled(event: RetrieverEvent, reranking_enabled: bool) -> bool:
    """Check if reranking step should run."""
    return isinstance(event, RetrieverEvent) and reranking_enabled


def check_reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, reranking_enabled: bool) -> bool:
    """Ensure ordering only happens after reranking is complete (or if disabled)."""
    if not reranking_enabled:
        return isinstance(event, RetrieverEvent)
    return isinstance(event, RerankerEvent)


def check_is_answer_response(event: AgentInTheLoop.response) -> bool:
    """Check if agent-in-the-loop response is a successful answer."""
    return isinstance(event.stop_event, AnswerStopEvent)


def check_is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Check if agent-in-the-loop response is an unsuccessful answer."""
    return isinstance(event.stop_event, NoAnswerStopEvent)


def check_context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """Check if context is ready for history limiting (RAGAgent version)."""
    return context_sufficient_event is not None


def check_context_ready_for_history_limit_with_expert(
    context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """Check if context is ready for history limiting (ExpertRAGAgent version)."""
    if isinstance(context_event, ExpertAnswerContextEvent):
        return True
    return context_sufficient_event is not None


def check_organization_memory_enabled(config: RAGAgentConfig) -> bool:
    """Check if organization memory retrieval is enabled in the agent configuration."""
    return config.memory.enable_organization_memory


def check_user_memory_retrieval_enabled(config: RAGAgentConfig) -> bool:
    """Check if user memory retrieval is enabled in the agent configuration."""
    return config.memory.enable_user_memory_retrieval


def check_user_memory_storage_enabled(config: RAGAgentConfig) -> bool:
    """Check if user memory storage is enabled in the agent configuration."""
    return config.memory.enable_user_memory_storage


def check_memory_ready_for_chat_history(
    config: RAGAgentConfig,
    user_memory_event: RetrieveUserMemoryEvent | None,
    org_memory_event: RetrieveOrganizationMemoryEvent | None,
) -> bool:
    """
    Check if all required memory events have been retrieved before extending chat history.

    Prevents race conditions by ensuring:
    - If user memory is enabled, wait for user memory event
    - If org memory is enabled, wait for org memory event
    - Only execute once when all required events are present
    """
    if config.memory.enable_user_memory_retrieval and user_memory_event is None:
        return False
    if config.memory.enable_organization_memory and org_memory_event is None:
        return False
    # If neither is enabled, return False - step shouldn't run at all
    return config.memory.enable_user_memory_retrieval or config.memory.enable_organization_memory


def check_memory_added_to_chat_history(
    config: RAGAgentConfig,
    memory_history_event: AddMemoryToChatHistoryEvent | None,
) -> bool:
    """
    Check if memory has been added to chat history when required.

    Prevents race conditions by ensuring:
    - If any memory is enabled, wait for memory history event
    - If no memory is enabled, proceed immediately (no wait)
    """
    if config.memory.enable_user_memory_retrieval or config.memory.enable_organization_memory:
        return memory_history_event is not None
    return True


def check_ready_for_stop(
    config: RAGAgentConfig,
    store_memory_event: StoreUserMemoryEvent | None,
) -> bool:
    """
    Check if all required steps are complete before stopping.

    Ensures that if memory storage is enabled, we wait for storage to complete
    before emitting the stop event.
    """
    if config.memory.enable_user_memory_storage:
        return store_memory_event is not None
    return True
