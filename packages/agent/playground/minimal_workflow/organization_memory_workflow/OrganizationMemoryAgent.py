from swiss_ai_hub.core.displayers.EventDisplayer import EventDisplayer
from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
from swiss_ai_hub.core.generative_ai.memory.AgentMemory import AgentMemory
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.nats.events.control.stop.StopEvent import StopEvent
from swiss_ai_hub.core.nats.events.memory.history.AddOrganizationMemoryToChatHistoryEvent import (
    AddOrganizationMemoryToChatHistoryEvent,
)
from swiss_ai_hub.core.nats.events.memory.retrieve.RetrieveOrganizationMemoryEvent import (
    RetrieveOrganizationMemoryEvent,
)
from swiss_ai_hub.core.nats.events.memory.store.StoreOrganizationMemoryEvent import StoreOrganizationMemoryEvent
from swiss_ai_hub.core.nats.events.semantic.llm.LLMEvent import LLMEvent
from swiss_ai_hub.core.nats.events.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.nats.topics import AgentInstanceTopic

from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgentConfig import (
    OrganizationMemoryAgentConfig,
)
from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class OrganizationMemoryAgent(Agent):
    """
    Organization memory management agent that stores and retrieves explicit organizational facts.

    Features:
    - Stores explicit organizational facts provided by users (not inferred from chat)
    - Retrieves relevant organization memories shared across all users
    - Extends chat history with organization memory context
    - Generates responses with organization memory awareness
    - Demonstrates organization namespace scoping (department-level isolation)

    Use this agent for managing shared organizational knowledge that should be accessible
    to all users within the organization namespace (e.g., company policies, tech stack,
    team conventions).

    ### Key Differences from UserMemoryAgent:
    - **Input**: Explicit facts (user provides clean memory text) vs. inferred from chat
    - **Scope**: Organization-wide (shared) vs. user-private
    - **Namespace**: Supports department-level scoping via tenant_namespace
    """

    @step()
    async def store_organization_memory_step(
        self,
        event: UserMessageEvent,
        memory: AgentMemory,
        topic: AgentInstanceTopic,
        agent_config: OrganizationMemoryAgentConfig,
    ) -> StoreOrganizationMemoryEvent:
        """Stores the user's query as an explicit organizational fact without LLM inference."""
        memory_added = await memory.add_organization_memory(
            memory=event.user_query,  # Direct storage - user query is the fact itself
            user_id=event.user.id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
            tenant_id=agent_config.tenant_id,
            tenant_namespace=agent_config.tenant_namespace,
        )
        return StoreOrganizationMemoryEvent.from_memory_added_object(memory_added=memory_added)

    @step()
    async def retrieve_organization_memory_step(
        self,
        event: UserMessageEvent,
        _: StoreOrganizationMemoryEvent,
        memory: AgentMemory,
        agent_config: OrganizationMemoryAgentConfig,
    ) -> RetrieveOrganizationMemoryEvent:
        """Searches organization memories to provide shared organizational context for the conversation."""
        memory_search_result = await memory.search_organization_memory(
            query=event.user_query,
            tenant_id=agent_config.tenant_id,
            tenant_namespace=agent_config.tenant_namespace,
            user_id=event.user.id,
        )
        return RetrieveOrganizationMemoryEvent.from_memory_search_result(memory_search_result=memory_search_result)

    @step()
    async def add_memory_to_chat_history_step(
        self, user_message_event: UserMessageEvent, memory_event: RetrieveOrganizationMemoryEvent, t: LocaleHandler
    ) -> AddOrganizationMemoryToChatHistoryEvent:
        """Prepends organization memories as system message to guide LLM responses with shared org context."""
        extended_chat_history = extend_chat_history_with_organization_memory(
            chat_history=user_message_event.messages,
            memories=memory_event.memories,
            relations=memory_event.relations,
            t=t,
        )
        return AddOrganizationMemoryToChatHistoryEvent(extended_history=extended_chat_history)

    @step()
    async def respond_with_memory_step(
        self,
        event: AddOrganizationMemoryToChatHistoryEvent,
        agent_config: OrganizationMemoryAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        """Generates response using memory-enhanced chat history with organizational context."""
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.extended_history, as_stop_step=False)

    @step()
    async def stop_step(self, _: LLMEvent) -> StopEvent:
        """Marks workflow completion and returns final response to user."""
        return StopEvent()
