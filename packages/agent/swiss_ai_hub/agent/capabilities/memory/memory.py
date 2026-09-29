from collections.abc import Sequence
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import (
    LLMEvent,
    MemoryRecalledEvent,
    MemoryStorageRequestedEvent,
    RecallMemoryEvent,
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
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class Memory(Capability):
    """
    User and organization memory, as one call and one delegation:

    - `recall(query)` is answered with `MemoryRecalledEvent`, one context block per scope, empty when memory is
      off for the profile or the run has no identity to read for, so a step waiting on it never hangs.
    - `remember(...)` builds the memory-storage delegation directly, with no step behind it. Return it from
      the same step as `Conversation.complete(...)`, ahead of it, and the list order is what guarantees the
      delegation is published before the run tears down (ADR `2026_09_11`).
    """

    calls: ClassVar[dict] = {RecallMemoryEvent: MemoryRecalledEvent}
    required_config: ClassVar[type[MemoryFields]] = MemoryFields

    Recall = RecallMemoryEvent
    Recalled = MemoryRecalledEvent

    @staticmethod
    def recall(query: str, org_memory_namespaces: Sequence[str] = ()) -> RecallMemoryEvent:
        return RecallMemoryEvent(query=query, org_memory_namespaces=list(org_memory_namespaces))

    @staticmethod
    def remember(
        query: str,
        answer: LLMEvent,
        user: UserIdentity | None,
        topic: AgentInstanceTopic,
        agent_config: AgentConfig,
        memory: MemoryFields,
        locale: str,
    ) -> MemoryStorageRequestedEvent | None:
        """The delegation that persists this turn, or None when the profile does not store memory or the run has
        no identity to attribute it to.

        The payload is the query plus the answer — never the final LLM input, whose context blocks and
        client-augmented message would feed document text into fact extraction (#1753).
        """
        if user is None or not query.strip() or not memory.user_memory.enable_user_memory_storage:
            return None
        conversation = [
            ChatMessage(role=MessageRole.USER, content=query),
            *(message.to_llama_index() for message in answer.output_messages or []),
        ]
        return build_memory_storage_request(
            user=user, messages=conversation, topic=topic, agent_config=agent_config, locale=locale
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.memory.steps.recall.name"),
        description=AgentLocaleString.from_i18n_path("agent.memory.steps.recall.description"),
        icon="mdi:brain",
    )
    async def recall_step(
        agent: Agent,
        request: RecallMemoryEvent,
        agent_config: AgentConfig,
        memory: MemoryFields,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[RetrieveUserMemoryEvent | RetrieveOrganizationMemoryEvent | MemoryRecalledEvent]:
        """Search both scopes and answer with their blocks; the retrieval events are what the chat displays."""
        if not request.query.strip():
            return [MemoryRecalledEvent()]
        events: list[RetrieveUserMemoryEvent | RetrieveOrganizationMemoryEvent | MemoryRecalledEvent] = []
        user_block: list[ChatMessage] = []
        organization_block: list[ChatMessage] = []

        if user is not None and memory.user_memory.enable_user_memory_retrieval:
            retrieved = await do_retrieve_user_memory(
                query=request.query,
                user_id=user.id,
                memory=build_agent_memory(agent, agent_config, memory, t),
                rerank=memory.user_memory.rerank_user_memory,
            )
            user_block = extend_chat_history_with_user_memory(
                chat_history=[], memories=retrieved.memories, relations=retrieved.relations, user=user, t=t
            )
            events.append(retrieved)

        if memory.org_memory is not None:
            retrieved = await do_retrieve_organization_memory(
                query=request.query,
                requested_namespaces=request.org_memory_namespaces,
                user_id=user.id if user else None,
                org_memory=memory.org_memory,
                memory=build_agent_memory(agent, agent_config, memory, t),
            )
            organization_block = extend_chat_history_with_organization_memory(
                chat_history=[], memories=retrieved.memories, t=t
            )
            events.append(retrieved)

        return [*events, MemoryRecalledEvent(user_block=user_block, organization_block=organization_block)]
