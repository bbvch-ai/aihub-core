"""The composition contract: what a blueprint gets from listing capabilities, and what stops it early.

Pinned on a throwaway blueprint rather than a production one so the assertions stay about the mechanism —
own steps plus contributed steps in one flat set, defaults withheld when the blueprint provides them, name
collisions and config mismatches refused before a run exists.
"""

from typing import ClassVar

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import (
    EnrichedChatHistoryEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    LLMStopEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_capability import ConversationCapability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.conversation.conversation_wiring import ConversationWiring
from swiss_ai_hub.agent.capabilities.memory.memory_capability import MemoryCapability
from swiss_ai_hub.agent.capabilities.self_awareness.self_awareness_capability import SelfAwarenessCapability
from swiss_ai_hub.agent.workflow.decorators.step import step


class BareChatAgent(Agent):
    """A spine-only blueprint: no detection, nothing that stops after the answer."""

    capabilities: ClassVar[tuple[type[Capability], ...]] = (ConversationCapability,)

    @step()
    async def limit_chat_history_step(self, event: UserMessageEvent) -> LimitChatHistoryEvent:
        return LimitChatHistoryEvent(limited_history=event.messages)

    @step()
    async def respond_step(self, event: EnrichedChatHistoryEvent) -> LLMEvent:
        return LLMEvent()


class OwnStopAgent(BareChatAgent):
    @step()
    async def stop_step(self, event: LLMEvent) -> LLMStopEvent:
        return LLMStopEvent()


class CollidingAgent(BareChatAgent):
    @step()
    async def derive_query_step(self, event: LimitChatHistoryEvent) -> None:
        return None


def _names(agent: type[Agent]) -> set[str]:
    return {step.__name__ for step in agent.get_steps()}


def test_contributed_steps_join_the_blueprints_own_in_one_flat_set():
    assert {step.__name__ for step in BareChatAgent.get_own_steps()} == {"limit_chat_history_step", "respond_step"}
    assert _names(BareChatAgent) == {
        "limit_chat_history_step",
        "respond_step",
        "open_gate_step",
        "derive_query_step",
        "assemble_context_step",
        "generate_conversation_title_step",
        "stop_step",
    }
    assert BareChatAgent.get_start_events() == {UserMessageEvent}
    assert LLMStopEvent in BareChatAgent.get_stop_events()


def test_the_gate_opener_is_withheld_when_detection_is_installed():
    assert "open_gate_step" in _names(BareChatAgent)
    for agent in (RAGAgent, LLMWrappingAgent):
        assert "open_gate_step" not in _names(agent)
        assert NotAMetaQuestionEvent in agent.get_output_events()


def test_the_default_stop_is_withheld_when_the_blueprint_stops_itself():
    spine_stop = ConversationCapability.stop_step
    assert spine_stop in BareChatAgent.get_steps()
    assert spine_stop in LLMWrappingAgent.get_steps()
    assert spine_stop not in OwnStopAgent.get_steps()
    assert spine_stop not in RAGAgent.get_steps()
    assert "stop_step" in _names(RAGAgent)


def test_barrier_counts_follow_the_installed_capabilities():
    assert ConversationWiring.count_enrichers(BareChatAgent) == 0
    assert ConversationWiring.count_post_answer_hooks(BareChatAgent) == 0
    for agent in (RAGAgent, LLMWrappingAgent):
        assert ConversationWiring.count_enrichers(agent) == 2
        assert ConversationWiring.count_post_answer_hooks(agent) == 1


def test_a_step_name_collision_is_refused():
    with pytest.raises(ValueError, match="two steps named 'derive_query_step'"):
        CollidingAgent.get_steps()


def test_a_config_that_misses_a_capability_base_is_refused_at_start():
    with pytest.raises(TypeError, match="MemoryCapability"):
        RAGAgent.validate_capabilities(ConversationFields)
    with pytest.raises(TypeError, match="ConversationCapability"):
        BareChatAgent.validate_capabilities(AgentConfig)


def test_production_blueprints_install_the_same_three_capabilities():
    for agent in (RAGAgent, LLMWrappingAgent):
        assert agent.capabilities == (ConversationCapability, SelfAwarenessCapability, MemoryCapability)
