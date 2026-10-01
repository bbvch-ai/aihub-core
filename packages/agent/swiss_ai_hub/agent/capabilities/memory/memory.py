import asyncio
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
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolDefinition,
    ToolResultEvent,
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
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

RECALL_MEMORY_TOOL = "recall_memory"


@precondition()
async def recalls_memory(call: ToolCallApprovedEvent) -> bool:
    return call.name == RECALL_MEMORY_TOOL


@precondition()
async def answers_a_recall_call(recalled: MemoryRecalledEvent, decided: ToolCallsDecidedEvent) -> bool:
    return recalled.tool_call_id is not None and recalled.tool_call_id in decided.tool_call_ids


class Memory(Capability):
    """
    User and organization memory, as one call and one delegation:

    - `recall(query)` is answered with `MemoryRecalledEvent`, one context block per scope, empty when memory is
      off for the profile or the run has no identity to read for, so a step waiting on it never hangs.
    - `remember(...)` builds the memory-storage delegation directly, with no step behind it. Return it from
      the same step as `Conversation.complete(...)`, ahead of it, and the list order is what guarantees the
      delegation is published before the run tears down (ADR `2026_09_11`).

    In a tool set, the model recalls what it needs when it needs it, through the same search, instead of every turn
    starting with what memory holds for the question.
    """

    calls: ClassVar[dict] = {RecallMemoryEvent: (MemoryRecalledEvent,)}
    required_config: ClassVar[type[MemoryFields]] = MemoryFields

    RecallRequest = RecallMemoryEvent
    Recalled = MemoryRecalledEvent

    tool_name: ClassVar[str] = RECALL_MEMORY_TOOL
    tool_options: ClassVar[ToolOptions] = ToolOptions(
        label=AgentLocaleString.from_i18n_path("agent.memory.tool.label"),
        approval_summary=AgentLocaleString.from_i18n_path("agent.memory.tool.approval_summary"),
    )

    @classmethod
    def tool_definition(cls, context: ToolContext) -> ToolDefinition | None:
        """Offered when the profile reads a memory scope the run can use: the user's needs a user to read for."""
        config = context.agent_config
        if not isinstance(config, MemoryFields):
            return None
        reads_user = context.user is not None and config.user_memory.enable_user_memory_retrieval
        if not reads_user and config.org_memory is None:
            return None
        t = context.t
        return ToolDefinition(
            name=RECALL_MEMORY_TOOL,
            description=t("agent.memory.tool.description"),
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": t("agent.memory.tool.query")}},
                "required": ["query"],
            },
        )

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
        """Search both scopes at once and answer with their blocks; the retrieval events are what the chat displays.

        The scopes run concurrently because each may wait out its own timeout, which one after the other would add
        up on every turn of a degraded memory backend.
        """
        if not request.query.strip():
            return [MemoryRecalledEvent(tool_call_id=request.tool_call_id)]
        user_retrieved, organization_retrieved = await asyncio.gather(
            Memory._recall_user(agent, request, agent_config, memory, t, user),
            Memory._recall_organization(agent, request, agent_config, memory, t, user),
        )
        user_block = (
            extend_chat_history_with_user_memory(
                chat_history=[],
                memories=user_retrieved.memories,
                relations=user_retrieved.relations,
                user=user,
                t=t,
            )
            if user_retrieved is not None and user is not None
            else []
        )
        organization_block = (
            extend_chat_history_with_organization_memory(chat_history=[], memories=organization_retrieved.memories, t=t)
            if organization_retrieved is not None
            else []
        )
        events = [event for event in (user_retrieved, organization_retrieved) if event is not None]
        return [
            *events,
            MemoryRecalledEvent(
                user_block=user_block, organization_block=organization_block, tool_call_id=request.tool_call_id
            ),
        ]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.memory.steps.recall_as_tool.name"),
        description=AgentLocaleString.from_i18n_path("agent.memory.steps.recall_as_tool.description"),
        icon="mdi:brain",
        precondition=recalls_memory,
    )
    async def tool_call_step(agent: Agent, call: ToolCallApprovedEvent) -> RecallMemoryEvent:
        """The model chose to recall: the regular recall, for the query it asked with."""
        return RecallMemoryEvent(query=str(call.arguments.get("query") or ""), tool_call_id=call.tool_call_id)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.memory.steps.answer_tool_call.name"),
        description=AgentLocaleString.from_i18n_path("agent.memory.steps.answer_tool_call.description"),
        icon="mdi:brain",
        precondition=answers_a_recall_call,
    )
    async def tool_result_step(
        agent: Agent, recalled: MemoryRecalledEvent, decided: ToolCallsDecidedEvent, t: LocaleHandler
    ) -> ToolResultEvent:
        """Hand what memory holds back to the loop: its text for the model, its blocks for a gathered answer."""
        block = [message for scope in recalled.blocks for message in scope]
        content = "\n\n".join(message.content for message in block if message.content)
        return ToolResultEvent(
            tool_call_id=recalled.tool_call_id,
            name=RECALL_MEMORY_TOOL,
            content=content or t("agent.memory.tool.nothing_remembered"),
            block=block,
        )

    @staticmethod
    async def _recall_user(
        agent: Agent,
        request: RecallMemoryEvent,
        agent_config: AgentConfig,
        memory: MemoryFields,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> RetrieveUserMemoryEvent | None:
        if user is None or not memory.user_memory.enable_user_memory_retrieval:
            return None
        return await do_retrieve_user_memory(
            query=request.query,
            user_id=user.id,
            memory=build_agent_memory(agent, agent_config, memory, t),
            rerank=memory.user_memory.rerank_user_memory,
        )

    @staticmethod
    async def _recall_organization(
        agent: Agent,
        request: RecallMemoryEvent,
        agent_config: AgentConfig,
        memory: MemoryFields,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> RetrieveOrganizationMemoryEvent | None:
        if memory.org_memory is None:
            return None
        return await do_retrieve_organization_memory(
            query=request.query,
            requested_namespaces=request.org_memory_namespaces,
            user_id=user.id if user else None,
            org_memory=memory.org_memory,
            memory=build_agent_memory(agent, agent_config, memory, t),
        )
