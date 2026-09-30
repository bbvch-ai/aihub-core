"""The composition contract: what returning a capability's request pulls in, and what refuses to run.

Pinned on throwaway blueprints so the assertions stay about the mechanism — a call composes the capability's
reachable steps, an unused call is pruned, and a blueprint that would stall, clash or run on the wrong config
is refused before a run exists.
"""

from typing import ClassVar

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import (
    LLMEvent,
    LLMStopEvent,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.agents.mcp_react_agent.configs.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.agents.mcp_react_agent.mcp_react_agent import McpReactAgent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.catalog import CapabilityCatalog
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.workflow.decorators.step import step


class EchoAgentConfig(ConversationFields, AgentConfig):
    pass


class EchoAgent(Agent):
    """Calls the conversation twice and nothing else."""

    @step()
    async def open_step(self, event: UserMessageEvent) -> Conversation.ContextualizeRequest:
        return Conversation.contextualize(history=event.messages, message=event)

    @step()
    async def respond_step(self, ctx: Conversation.Contextualized) -> Conversation.CompleteRequest:
        return Conversation.complete(answer=LLMEvent())


class ForgetfulAgent(Agent):
    """Calls the conversation but never picks the result up."""

    @step()
    async def open_step(self, event: UserMessageEvent) -> Conversation.ContextualizeRequest:
        return Conversation.contextualize(history=event.messages, message=event)


class ClashingAgent(EchoAgent):
    @step()
    async def derive_query_step(self, ctx: Conversation.Contextualized) -> None:
        return None


def _names(agent: type[Agent]) -> set[str]:
    return {step.__name__ for step in agent.get_steps()}


def test_returning_a_request_installs_the_capability_it_belongs_to():
    assert EchoAgent.installed_capabilities() == [Conversation]
    assert {step.__name__ for step in EchoAgent.get_own_steps()} == {"open_step", "respond_step"}
    assert {"inspect_message_step", "derive_query_step", "complete_conversation_step"} <= _names(EchoAgent)
    assert not any(step in EchoAgent.get_steps() for step in Memory.own_steps())


def test_a_call_the_blueprint_never_makes_is_pruned_with_everything_behind_it():
    assert "compose_context_step" not in _names(EchoAgent)
    assert "compose_context_step" not in _names(FewShotAgent)
    assert "compose_context_step" in _names(RAGAgent)


def test_a_result_nobody_consumes_is_refused():
    with pytest.raises(ValueError, match="no step consumes its result ConversationContextualizedEvent"):
        ForgetfulAgent.validate_workflow(EchoAgentConfig)


def test_a_config_without_the_mixin_is_refused():
    with pytest.raises(ValueError, match="AgentConfig must list ConversationFields as a base"):
        EchoAgent.validate_workflow(AgentConfig)
    EchoAgent.validate_workflow(EchoAgentConfig)


def test_a_step_name_collision_is_refused():
    with pytest.raises(ValueError, match="two steps are named 'derive_query_step'"):
        ClashingAgent.validate_workflow(EchoAgentConfig)


@pytest.mark.parametrize(
    ("agent", "config"),
    [
        (RAGAgent, RAGAgentConfig),
        (ExpertRAGAgent, ExpertRAGAgentConfig),
        (LLMWrappingAgent, LLMWrappingAgentConfig),
        (FewShotAgent, FewShotAgentConfig),
        (McpReactAgent, McpReactAgentConfig),
    ],
    ids=lambda value: getattr(value, "__name__", value),
)
def test_every_conversational_blueprint_validates(agent: type[Agent], config: type[AgentConfig]):
    agent.validate_workflow(config)
    assert {capability.__name__ for capability in agent.installed_capabilities()} == {"Conversation", "Memory"}


class SearchEvent(ControlEvent):
    pass


class FoundEvent(ControlEvent):
    pass


class NeedsClarificationEvent(ControlEvent):
    pass


class ExpiredEvent(ControlEvent):
    pass


class Search(Capability):
    """Answers a search with a hit or a question back, and may give up on the turn."""

    calls: ClassVar[dict] = {SearchEvent: (FoundEvent, NeedsClarificationEvent, LLMStopEvent)}

    @staticmethod
    @step()
    async def search_step(agent: Agent, request: SearchEvent) -> FoundEvent | NeedsClarificationEvent | LLMStopEvent:
        return FoundEvent()


class StaleSearch(Search):
    calls: ClassVar[dict] = {SearchEvent: (FoundEvent, NeedsClarificationEvent, LLMStopEvent, ExpiredEvent)}


class HalfHandlingAgent(Agent):
    @step()
    async def open_step(self, event: UserMessageEvent) -> SearchEvent:
        return SearchEvent()

    @step()
    async def answer_step(self, found: FoundEvent) -> StopEvent:
        return StopEvent()


class FullyHandlingAgent(HalfHandlingAgent):
    @step()
    async def ask_back_step(self, question: NeedsClarificationEvent) -> StopEvent:
        return StopEvent()


@pytest.fixture
def search_capability(monkeypatch: pytest.MonkeyPatch):
    def install(capability: type[Capability]) -> None:
        monkeypatch.setattr(CapabilityCatalog, "all", staticmethod(lambda: [Conversation, Memory, capability]))

    return install


class TestSeveralOutcomes:
    def test_every_outcome_that_does_not_end_the_run_must_be_consumed(self, search_capability):
        search_capability(Search)

        with pytest.raises(ValueError, match="no step consumes its result NeedsClarificationEvent"):
            HalfHandlingAgent.validate_workflow(AgentConfig)
        FullyHandlingAgent.validate_workflow(AgentConfig)

    def test_an_outcome_no_step_emits_is_refused(self, search_capability):
        class StaleSearchingAgent(FullyHandlingAgent):
            @step()
            async def expired_step(self, expired: ExpiredEvent) -> StopEvent:
                return StopEvent()

        search_capability(StaleSearch)

        with pytest.raises(ValueError, match="declares ExpiredEvent as an outcome of SearchEvent, but none"):
            StaleSearchingAgent.validate_workflow(AgentConfig)

    def test_an_undeclared_way_to_end_the_call_is_refused(self, search_capability):
        class QuietSearch(Search):
            calls: ClassVar[dict] = {SearchEvent: (FoundEvent, NeedsClarificationEvent)}

        class QuietlySearchingAgent(FullyHandlingAgent):
            pass

        search_capability(QuietSearch)

        with pytest.raises(ValueError, match="can end SearchEvent with LLMStopEvent, but does not declare it"):
            QuietlySearchingAgent.validate_workflow(AgentConfig)


def test_the_meta_question_answer_is_a_declared_outcome_of_contextualize():
    assert LLMStopEvent in Conversation.calls[Conversation.ContextualizeRequest]
