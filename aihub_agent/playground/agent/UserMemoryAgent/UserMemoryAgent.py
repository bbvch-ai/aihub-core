from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.chat_history.extend_chat_history_with_user_memory import (
    extend_chat_history_with_user_memory,
)
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import LLMEvent, NewMemoryEvent, StopEvent, UserMessageEvent
from aihub_lib.nats.events.common.AddUserMemoryToChatHistoryEvent import AddUserMemoryToChatHistoryEvent
from aihub_lib.nats.events.memory.RetrieveUserMemoryEvent import RetrieveUserMemoryEvent
from aihub_lib.nats.topics import AgentInstanceTopic

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.agent.UserMemoryAgent.UserMemoryAgentConfig import UserMemoryAgentConfig


class UserMemoryAgent(Agent):
    """
    Memory-enhanced conversational agent that retrieves and persists user memories.

    Features:
    - Retrieves relevant memories from mem0 based on user query
    - Extends chat history with memory context as system message
    - Generates responses with memory awareness
    - Persists new memories from conversation to mem0

    Use this agent for personalized conversations requiring long-term context
    beyond single session chat history.
    """

    @step()
    async def retrieve_memory_step(
        self,
        event: UserMessageEvent,
        memory: AgentMemory,
    ) -> RetrieveUserMemoryEvent:
        """Searches user memories to provide personalized context for the conversation."""
        memory_search_result = await memory.search_user_memory(query=event.user_query, user_id=event.user.id)
        return RetrieveUserMemoryEvent.from_memory_search_result(memory_search_result=memory_search_result)

    @step()
    async def add_memory_to_chat_history_step(
        self, user_message_event: UserMessageEvent, memory_event: RetrieveUserMemoryEvent, t: LocaleHandler
    ) -> AddUserMemoryToChatHistoryEvent:
        """Prepends memories as system message to guide LLM responses with long-term user context."""
        extended_chat_history = extend_chat_history_with_user_memory(
            chat_history=user_message_event.messages,
            memories=memory_event.memories,
            relations=memory_event.relations,
            user=user_message_event.user,
            t=t,
        )
        return AddUserMemoryToChatHistoryEvent(extended_history=extended_chat_history)

    @step()
    async def respond_with_memory_step(
        self,
        event: AddUserMemoryToChatHistoryEvent,
        agent_config: UserMemoryAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        """Generates response using memory-enhanced chat history for personalized replies."""
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.extended_history, as_stop_step=False)

    @step()
    async def update_memory_step(
        self,
        user_message_event: UserMessageEvent,
        llm_event: LLMEvent,
        memory: AgentMemory,
        topic: AgentInstanceTopic,
    ) -> NewMemoryEvent:
        """Persists conversation learnings to long-term memory for future interactions."""
        memory_added = await memory.add_user_memory(
            messages=llm_event.chat_messages,
            user_id=user_message_event.user.id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        return NewMemoryEvent.from_memory_added_object(memory_added=memory_added)

    @step()
    async def stop_step(self, _: NewMemoryEvent) -> StopEvent:
        """Marks workflow completion and returns final response to user."""
        return StopEvent()
