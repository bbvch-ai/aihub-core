import asyncio
import logging

from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import (
    MemoryStorageRequestedEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieveUserMemoryEvent,
    StoreUserMemoryRequestedEvent,
)
from swiss_ai_hub.core.generative_ai import AgentMemory, OrgMemoryNamespaceResolver, OrgMemoryReadConfig
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.memory_writer_agent.configs.memory_writer_agent_config import MemoryWriterAgentConfig

logger = logging.getLogger(__name__)

# Bounds a hung backend, not normal latency: well above the ~0.25s graph-free median from issue #1713.
MEMORY_RETRIEVAL_TIMEOUT_SECONDS = 15.0


def build_agent_memory(agent: Agent, agent_config: AgentConfig, t: LocaleHandler) -> AgentMemory:
    """The same `AgentMemory` the dispatcher would inject, built only on the turns that actually read memory.

    Constructing it here rather than declaring it as a step parameter keeps a profile with memory switched off
    from ever configuring the memory service.
    """
    return AgentMemory(
        agent_config=agent_config,
        agent_class=type(agent).__name__,
        t=t,
        llm_model_name=agent_config.memory_llm_model_name,
    )


async def do_retrieve_user_memory(
    query: str,
    user_id: str,
    memory: AgentMemory,
    rerank: bool,
) -> RetrieveUserMemoryEvent:
    """Retrieve user memories for personalized context.

    Searches with the turn's query, never the raw last user message — chat clients running full-context RAG
    inline whole documents into that message (issue #1753).

    A failing memory subsystem degrades to an empty event instead of propagating (issue #1713): raising
    would end the run, while `stop_on_error=False` would suppress the `ExceptionEvent` but emit nothing at
    all — and the context join waits for this enricher's block, so the run would hang. A hung backend
    degrades the same way, since a stall blocks the chat turn just as a raise ends it.
    """
    try:
        memory_result = await asyncio.wait_for(
            memory.search_user_memory(
                query=query,
                user_id=user_id,
                limit=10,
                threshold=0.5,
                rerank=rerank,
            ),
            timeout=MEMORY_RETRIEVAL_TIMEOUT_SECONDS,
        )
    except Exception:
        logger.warning(
            "User memory retrieval failed; answering without user memory. user_id=%s",
            user_id,
            exc_info=True,
        )
        return RetrieveUserMemoryEvent(memories=[], relations=[])

    return RetrieveUserMemoryEvent.from_memory_search_result(memory_result)


async def do_retrieve_organization_memory(
    query: str,
    requested_namespaces: list[str],
    user_id: str | None,
    org_memory: OrgMemoryReadConfig,
    memory: AgentMemory,
) -> RetrieveOrganizationMemoryEvent:
    """Retrieve organization memories for shared expert-knowledge context.

    Searches with the turn's query for the same reason as `do_retrieve_user_memory` (issue #1753). Degrades
    to an empty event on failure for the same reason as well. Organization memory is tenant-scoped and runs
    without an identity — `user_id` exists only for the degradation log line, so an identity-less delegated
    run passes `None` rather than dereferencing an absent user.

    Namespace resolution is deliberately left outside that safety net: a start event asking for a namespace
    outside the configured allow-list is a caller error, and silently answering from the wrong scope (or
    from none) would hide it. Only the memory-subsystem call degrades.
    """
    tenant_namespaces = OrgMemoryNamespaceResolver.resolve_for_search(
        requested=requested_namespaces,
        configured=org_memory.allowed_tenant_namespaces,
    )
    try:
        memory_result = await asyncio.wait_for(
            memory.search_organization_memory(
                query=query,
                tenant_id=org_memory.tenant_id,
                tenant_namespaces=tenant_namespaces,
                user_id=None,
                limit=10,
                threshold=0.5,
                rerank=org_memory.rerank_organization_memory,
            ),
            timeout=MEMORY_RETRIEVAL_TIMEOUT_SECONDS,
        )
    except Exception:
        logger.warning(
            "Organization memory retrieval failed; answering without organization memory. "
            "tenant_id=%s namespaces=%s user_id=%s",
            org_memory.tenant_id,
            tenant_namespaces,
            user_id,
            exc_info=True,
        )
        return RetrieveOrganizationMemoryEvent(memories=[], relations=[])

    return RetrieveOrganizationMemoryEvent.from_memory_search_result(memory_result)


def build_memory_storage_request(
    user: UserIdentity,
    messages: list[ChatMessage],
    topic: AgentInstanceTopic,
    agent_config: AgentConfig,
    locale: str,
) -> MemoryStorageRequestedEvent:
    """
    Build the detached memory-storage delegation targeting the `MemoryWriterAgent` (issue #1179).

    Carries the originating agent's identity (from the topic + config) so the writer rebuilds the *same*
    `AgentMemory` — preserving the fact-extraction prompt and the `_agent_id` scoping tag.
    """
    return MemoryStorageRequestedEvent(
        start_event=StoreUserMemoryRequestedEvent(
            user=user,
            messages=messages,
            locale=locale,
            origin_thread_id=topic.thread_id,
            origin_display_id=topic.display_id,
            origin_run_id=topic.run_id,
            origin_agent_class=topic.agent_class,
            origin_agent_id=agent_config.agent_id,
            origin_agent_name=agent_config.name,
            origin_agent_description=agent_config.description,
            origin_memory_llm=agent_config.memory_llm_model_name,
        ),
        # Routing target carried on the event (not hard-coded in the dispatcher by design) so the delegation
        # primitive stays generic; today it resolves to the single MemoryWriterAgent system instance.
        target_agent_class=MemoryWriterAgentConfig.AGENT_CLASS,
        target_agent_id=MemoryWriterAgentConfig.AGENT_ID,
    )
