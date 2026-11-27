"""Agents as tools: the model is offered exactly the agents its user may use, calls one with a request, and gets its
answer, failure or silence back as the tool result."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from swiss_ai_hub.core.agents import AgentConfig, AgentRef
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    ExceptionEvent,
    RAGSuccessStopEvent,
    ToolCallApprovedEvent,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.rpc import CallableAgent
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.agent_tools.agent_tool_choice import AgentToolChoice
from swiss_ai_hub.agent.capabilities.agent_tools.agent_tool_fields import AgentToolFields
from swiss_ai_hub.agent.capabilities.agent_tools.agent_tools import AgentTools, answers_an_agent_call
from swiss_ai_hub.agent.capabilities.agent_tools.agent_tools_config import AgentToolsConfig
from swiss_ai_hub.agent.capabilities.agent_tools.offered_agents import TOOL_NAME_LIMIT, OfferedAgents
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_availability import ToolAvailability
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig

T = LocaleHandler("en")
CALLER = AgentInstanceTopic(
    agent_class="UniversalAgent",
    agent_id="assistant",
    thread_id="thread",
    display_id="display",
    run_id="run",
    event_type="control_event",
    event_name="RunToolLoopEvent",
    event_id="event",
)


class _Context:
    def __init__(self, values: dict | None = None) -> None:
        self.values = dict(values or {})

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value


class _Access:
    def __init__(self, *allowed: tuple[str, str]) -> None:
        self.allowed = set(allowed)

    def has_access_to_agent(self, agent_class: str, agent_id: str) -> bool:
        return (agent_class, agent_id) in self.allowed


class _Agents:
    def __init__(self, *agents: CallableAgent) -> None:
        self.agents = list(agents)

    async def online_agents(self) -> list[CallableAgent]:
        return self.agents


class CallerConfig(AgentToolFields, AgentConfig):
    pass


class CallerAgent(Agent):
    tools = ToolLoop.over(AgentTools)


def _agent(agent_class: str, agent_id: str, conversational: bool = True) -> CallableAgent:
    return CallableAgent(
        agent_class=agent_class,
        agent_id=agent_id,
        name=LocaleString(en=f"{agent_id} agent"),
        description=LocaleString(en=f"Answers questions about {agent_id}."),
        is_conversational=conversational,
    )


LAW = _agent("RAGAgent", "law")
HR = _agent("RAGAgent", "hr")
IMAP = _agent("ImapAgent", "mailbox", conversational=False)
SELF = _agent("UniversalAgent", "assistant")


def _config(**settings: Any) -> CallerConfig:
    return CallerConfig(
        agent_class="UniversalAgent",
        agent_id="assistant",
        name=LocaleString(en="Assistant"),
        description=LocaleString(en="Assistant"),
        agent_tools=AgentToolsConfig(**settings),
    )


def _tool_context(config: CallerConfig, access: Any, run_context: _Context, *agents: CallableAgent) -> ToolContext:
    return ToolContext.model_construct(
        agent_config=config,
        displayer=MagicMock(),
        t=T,
        user=fake_user(),
        access=access,
        topic=CALLER,
        callable_agents=_Agents(*agents),
        run_context=run_context,
    )


class TestOffered:
    @pytest.mark.asyncio
    async def test_only_conversational_agents_the_user_may_use_are_offered_and_never_the_caller(self):
        run_context = _Context()
        access = _Access(("RAGAgent", "law"), ("ImapAgent", "mailbox"), ("UniversalAgent", "assistant"))

        definitions = await AgentTools.tool_definitions(
            _tool_context(_config(), access, run_context, LAW, HR, IMAP, SELF)
        )

        assert [definition.name for definition in definitions] == ["ask_agent__law"]
        assert "law agent" in definitions[0].description
        assert definitions[0].parameters["required"] == ["message"]

    @pytest.mark.asyncio
    async def test_a_profile_listing_its_agents_offers_only_those(self):
        access = _Access(("RAGAgent", "law"), ("RAGAgent", "hr"))
        config = _config(
            only_listed=True, agents=[AgentToolChoice(agent=AgentRef(agent_class="RAGAgent", agent_id="hr"))]
        )

        definitions = await AgentTools.tool_definitions(_tool_context(config, access, _Context(), LAW, HR))

        assert [definition.name for definition in definitions] == ["ask_agent__hr"]

    @pytest.mark.asyncio
    async def test_a_profile_without_the_setting_or_a_run_without_a_user_offers_none(self):
        access = _Access(("RAGAgent", "law"))
        off = CallerConfig(
            agent_class="UniversalAgent",
            agent_id="assistant",
            name=LocaleString(en="A"),
            description=LocaleString(en="A"),
        )

        assert await AgentTools.tool_definitions(_tool_context(off, access, _Context(), LAW)) == []
        assert await AgentTools.tool_definitions(_tool_context(_config(), None, _Context(), LAW)) == []

    @pytest.mark.asyncio
    async def test_a_run_at_the_end_of_a_chain_of_delegations_offers_none(self):
        run_context = _Context({"delegated_by": {"depth": 2}})

        definitions = await AgentTools.tool_definitions(
            _tool_context(_config(max_depth=2), _Access(("RAGAgent", "law")), run_context, LAW)
        )

        assert definitions == []

    def test_tool_names_are_unique_and_within_the_limit(self):
        long_id = "x" * 80
        agents = [_agent("RAGAgent", long_id), _agent("FewShotAgent", long_id)]
        access = _Access(*((agent.agent_class, agent.agent_id) for agent in agents))

        chosen = OfferedAgents.choose(agents, AgentToolsConfig(), access, CALLER, "ask_agent")

        names = [offered.tool_name for offered, _ in chosen]
        assert len(set(names)) == 2
        assert all(len(name) <= TOOL_NAME_LIMIT for name in names)

    @pytest.mark.asyncio
    async def test_each_agent_is_labelled_by_its_name_and_approved_by_its_own_policy(self):
        run_context = _Context()
        config = _config(
            default_approval=ToolApprovalPolicy.NEVER,
            agents=[
                AgentToolChoice(
                    agent=AgentRef(agent_class="RAGAgent", agent_id="law"), approval=ToolApprovalPolicy.EVERY_CALL
                )
            ],
        )
        await AgentTools.tool_definitions(
            _tool_context(config, _Access(("RAGAgent", "law"), ("RAGAgent", "hr")), run_context, LAW, HR)
        )

        law = await CallerAgent.tools.options_in_run("ask_agent__law", run_context)
        hr = await CallerAgent.tools.options_in_run("ask_agent__hr", run_context)

        assert law.label_in("ask_agent__law", "en") == "law agent"
        assert law.default_approval == ToolApprovalPolicy.EVERY_CALL
        assert hr.default_approval == ToolApprovalPolicy.NEVER
        assert law.summary_in({"message": "Is it legal?"}, "en") == "Ask law agent: Is it legal?"


class TestFamilyInTheLoop:
    def test_a_member_belongs_to_the_set_offering_its_family(self):
        assert CallerAgent.tool_set_offering("ask_agent__law") is CallerAgent.tools
        assert CallerAgent.tools.kind("ask_agent__law") == "capability"
        assert CallerAgent.tools.family_of("ask_agent__law") == "ask_agent"
        assert CallerAgent.tool_set_offering("ask_agentlaw") is None

    @pytest.mark.asyncio
    async def test_disabling_the_family_withholds_every_member(self):
        config = ToolLoopConfig(disabled_tools=["ask_agent"], disable_tools=True)

        allowed = await ToolAvailability.allows("ask_agent__law", CallerAgent.tools, config, _Context(), CallerAgent)

        assert allowed is False


class TestCall:
    @pytest.mark.asyncio
    async def test_a_call_starts_the_offered_agent_for_the_asking_user_on_its_own_thread(self):
        run_context = _Context()
        config = _config(timeout_seconds=60)
        await AgentTools.tool_definitions(_tool_context(config, _Access(("RAGAgent", "law")), run_context, LAW))
        call = ToolCallApprovedEvent(
            tool_call_id="call-1", name="ask_agent__law", arguments={"message": "Is it legal?"}, kind="capability"
        )

        request = await AgentTools.ask_agent_step(CallerAgent(), call, config, run_context, T, fake_user())

        assert request.is_aitl_request_event
        assert (request.other_agent_topic.agent_class, request.other_agent_topic.agent_id) == ("RAGAgent", "law")
        assert request.tool_call_id == "call-1"
        assert request.timeout_seconds == 60
        assert not request.share_thread_id and not request.share_display_id
        assert request.start_event.user.id == fake_user().id
        assert request.start_event.messages[-1].content == "Is it legal?"

    @pytest.mark.asyncio
    async def test_an_agent_that_was_not_offered_is_never_called(self):
        call = ToolCallApprovedEvent(
            tool_call_id="call-1", name="ask_agent__hr", arguments={"message": "Salary?"}, kind="capability"
        )

        result = await AgentTools.ask_agent_step(CallerAgent(), call, _config(), _Context(), T, fake_user())

        assert result.is_error and result.tool_call_id == "call-1"


class TestAnswer:
    async def _pending(self) -> tuple[_Context, str]:
        run_context = _Context()
        config = _config(timeout_seconds=30)
        await AgentTools.tool_definitions(_tool_context(config, _Access(("RAGAgent", "law")), run_context, LAW))
        call = ToolCallApprovedEvent(
            tool_call_id="call-1", name="ask_agent__law", arguments={"message": "Is it legal?"}, kind="capability"
        )
        request = await AgentTools.ask_agent_step(CallerAgent(), call, config, run_context, T, fake_user())
        return run_context, request.event_id

    @pytest.mark.asyncio
    async def test_the_agent_s_answer_text_is_the_tool_result(self):
        run_context, request_event_id = await self._pending()
        answer = AgentInTheLoop.response(
            stop_event=RAGSuccessStopEvent(answer="Yes."), request_event_id=request_event_id
        )

        assert await answers_an_agent_call(answer, run_context)
        result = await AgentTools.agent_answered_step(CallerAgent(), answer, run_context, T)

        assert (result.tool_call_id, result.name, result.content, result.is_error) == (
            "call-1",
            "ask_agent__law",
            "Yes.",
            False,
        )

    @pytest.mark.asyncio
    async def test_a_failure_or_a_timeout_comes_back_as_an_error_and_the_run_continues(self):
        run_context, request_event_id = await self._pending()
        failure = AgentInTheLoop.exception(
            exception_event=ExceptionEvent(message="boom"), request_event_id=request_event_id
        )
        timeout = AgentInTheLoop.timeout(request_event_id=request_event_id, timeout_seconds=30)

        failed = await AgentTools.agent_answered_step(CallerAgent(), failure, run_context, T)
        silent = await AgentTools.agent_answered_step(CallerAgent(), timeout, run_context, T)

        assert failed.is_error and "boom" in failed.content
        assert silent.is_error and "30" in silent.content

    @pytest.mark.asyncio
    async def test_answers_to_other_delegations_are_left_alone(self):
        answer = AgentInTheLoop.response(stop_event=RAGSuccessStopEvent(answer="Yes."), request_event_id="other")

        assert not await answers_an_agent_call(answer, _Context())
