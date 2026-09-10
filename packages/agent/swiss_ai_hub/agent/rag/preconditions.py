from swiss_ai_hub.core.events.agent import (
    AddMemoryToChatHistoryEvent,
    AgentInTheLoop,
    ContextSufficientAcceptEvent,
    MemoryStorageRequestedEvent,
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
    """Check if organization memory retrieval is enabled (org_memory config present)."""
    return config.org_memory is not None


def check_user_memory_retrieval_enabled(config: RAGAgentConfig, has_user: bool) -> bool:
    """Check if user memory retrieval is enabled in the agent configuration and there is a user to scope it to.

    `has_user` is not a second switch an admin sets — it is whether this run has an identity at all.
    `RAGStartEvent.user` is optional, so a run delegated by a scheduled agent has none, and user memory is
    per-user by definition: without an identity the only alternatives are reading nobody's memories (this) or
    reading a shared identity's, which is how one mailbox's context ends up in another customer's answer.
    """
    return config.user_memory.enable_user_memory_retrieval and has_user


def check_user_memory_storage_enabled(config: RAGAgentConfig, has_user: bool) -> bool:
    """Check if user memory storage is enabled and there is a user to attribute the write to.

    Gated on the identity for the same reason as retrieval, and more sharply: a write under a shared identity
    is not merely a bad answer this once, it is a bad answer for everyone who reads that identity afterwards.
    """
    return config.user_memory.enable_user_memory_storage and has_user


def check_memory_ready_for_chat_history(
    config: RAGAgentConfig,
    has_user: bool,
    user_memory_event: RetrieveUserMemoryEvent | None,
    org_memory_event: RetrieveOrganizationMemoryEvent | None,
) -> bool:
    """
    Check if all required memory events have been retrieved before extending chat history.

    Prevents race conditions by ensuring:
    - If user memory is enabled, wait for user memory event
    - If org memory is enabled, wait for org memory event
    - Only execute once when all required events are present

    The user-memory half has to agree with `check_user_memory_retrieval_enabled` about `has_user`, or an
    identity-less run waits forever for an event the skipped retrieval step never emits. Organization memory
    is unaffected: it is scoped to a tenant, which comes from the agent's own profile, not from the caller.
    """
    user_enabled = check_user_memory_retrieval_enabled(config, has_user)
    org_enabled = config.org_memory is not None
    if user_enabled and user_memory_event is None:
        return False
    if org_enabled and org_memory_event is None:
        return False
    return user_enabled or org_enabled


def check_memory_added_to_chat_history(
    config: RAGAgentConfig,
    has_user: bool,
    memory_history_event: AddMemoryToChatHistoryEvent | None,
) -> bool:
    """
    Check if memory has been added to chat history when required.

    Prevents race conditions by ensuring:
    - If any memory is enabled, wait for memory history event
    - If no memory is enabled, proceed immediately (no wait)
    """
    if check_user_memory_retrieval_enabled(config, has_user) or config.org_memory is not None:
        return memory_history_event is not None
    return True


def check_ready_for_stop(
    config: RAGAgentConfig,
    has_user: bool,
    store_memory_event: StoreUserMemoryEvent | None,
    memory_storage_request: MemoryStorageRequestedEvent | None = None,
) -> bool:
    """
    Check if all required steps are complete before stopping.

    When memory storage is enabled, gate the stop until the storage step has produced its event so the
    stop cannot race the store step (both trigger off the LLMEvent). In async mode
    (`enable_async_memory_storage`) the store step returns a `MemoryStorageRequestedEvent` — a
    millisecond-cheap delegation marker, NOT storage completion — so the run finalizes as soon as the answer
    is ready (issue #1179). In inline mode it returns a `StoreUserMemoryEvent` only after the write finishes.

    This is the gate that makes the identity check load-bearing rather than cosmetic: without agreeing with
    `check_user_memory_storage_enabled` about `has_user`, an identity-less run would answer correctly and then
    never terminate, waiting at its terminal step for a write that was deliberately skipped.
    """
    if not check_user_memory_storage_enabled(config, has_user):
        return True
    if config.user_memory.enable_async_memory_storage:
        return memory_storage_request is not None
    return store_memory_event is not None
