from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextBlockEvent,
    ConversationQueryEvent,
    LLMEvent,
    MemoryStorageRequestedEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieveUserMemoryEvent,
)
from swiss_ai_hub.core.generative_ai import (
    extend_chat_history_with_organization_memory,
    extend_chat_history_with_user_memory,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.capabilities.memory.memory_step_functions import (
    build_agent_memory,
    build_memory_storage_request,
    do_retrieve_organization_memory,
    do_retrieve_user_memory,
)
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step

USER_MEMORY = "user_memory"
ORGANIZATION_MEMORY = "organization_memory"


class MemoryCapability(Capability):
    """
    User and organization memory on the conversational spine: two enrichers that contribute context blocks
    for the turn's query, and one post-answer hook that delegates the user-memory write.

    Every step runs on every turn and reports even when memory is off for the profile or the run has no
    identity to read for — an empty block, or a bare post-processed marker — so the spine's join and stop
    barriers count reports instead of re-deriving the memory switches.
    """

    required_config: ClassVar[type[MemoryFields]] = MemoryFields

    # A programmatic start that narrows the organization-memory scope writes the requested namespaces here
    # in its entry step. The capability cannot name that start event, so the run context is the handover.
    REQUESTED_ORG_NAMESPACES_KEY: ClassVar[str] = "memory.requested_org_namespaces"

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.memory.steps.retrieve_user_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.memory.steps.retrieve_user_memory.description"),
        icon="mdi:account-circle",
    )
    async def retrieve_user_memory_step(
        agent: Agent,
        query: ConversationQueryEvent,
        agent_config: AgentConfig,
        memory: MemoryFields,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[ContextBlockEvent | RetrieveUserMemoryEvent]:
        """Contribute the user's memories as a context block, empty when memory is off or there is no identity."""
        if user is None or query.is_blank or not memory.user_memory.enable_user_memory_retrieval:
            return [ContextBlockEvent.empty(USER_MEMORY)]
        retrieved = await do_retrieve_user_memory(
            query=query.query,
            user_id=user.id,
            memory=build_agent_memory(agent, agent_config, memory, t),
            rerank=memory.user_memory.rerank_user_memory,
        )
        block = extend_chat_history_with_user_memory(
            chat_history=[], memories=retrieved.memories, relations=retrieved.relations, user=user, t=t
        )
        return [retrieved, ContextBlockEvent(source=USER_MEMORY, messages=block)]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.memory.steps.retrieve_organization_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.memory.steps.retrieve_organization_memory.description"),
        icon="mdi:brain",
    )
    async def retrieve_organization_memory_step(
        agent: Agent,
        query: ConversationQueryEvent,
        agent_config: AgentConfig,
        memory: MemoryFields,
        t: LocaleHandler,
        run_context: RunContext,
        user: UserIdentity | None = None,
    ) -> list[ContextBlockEvent | RetrieveOrganizationMemoryEvent]:
        """Contribute the organization's memories as a context block, empty when the profile reads none."""
        if memory.org_memory is None or query.is_blank:
            return [ContextBlockEvent.empty(ORGANIZATION_MEMORY)]
        requested = await run_context.get(MemoryCapability.REQUESTED_ORG_NAMESPACES_KEY, [])
        retrieved = await do_retrieve_organization_memory(
            query=query.query,
            requested_namespaces=requested,
            user_id=user.id if user else None,
            org_memory=memory.org_memory,
            memory=build_agent_memory(agent, agent_config, memory, t),
        )
        block = extend_chat_history_with_organization_memory(chat_history=[], memories=retrieved.memories, t=t)
        return [retrieved, ContextBlockEvent(source=ORGANIZATION_MEMORY, messages=block)]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.memory.steps.store_user_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.memory.steps.store_user_memory.description"),
        icon="mdi:content-save",
    )
    async def store_user_memory_step(
        agent: Agent,
        llm_event: LLMEvent,
        query: ConversationQueryEvent,
        agent_config: AgentConfig,
        memory: MemoryFields,
        topic: AgentInstanceTopic,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[MemoryStorageRequestedEvent | AnswerPostProcessedEvent]:
        """
        Delegate the user-memory write to the `MemoryWriterAgent` on its own run (issue #1179), then report.

        The payload is the turn's query plus the answer — never the final LLM input, whose system-role context
        blocks and client-augmented message would feed document text into fact extraction (#1753). The
        delegation request goes out ahead of the marker, so the stop step can never overtake it.
        """
        done = AnswerPostProcessedEvent(source=USER_MEMORY)
        if user is None or query.is_blank or not memory.user_memory.enable_user_memory_storage:
            return [done]
        conversation = [
            ChatMessage(role=MessageRole.USER, content=query.query),
            *(message.to_llama_index() for message in llm_event.output_messages or []),
        ]
        request = build_memory_storage_request(
            user=user, messages=conversation, topic=topic, agent_config=agent_config, locale=t.locale
        )
        return [request, done]
