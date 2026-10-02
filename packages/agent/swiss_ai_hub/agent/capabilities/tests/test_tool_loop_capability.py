"""The tool loop's contract: the model is offered exactly the tools the blueprint declares and the profile, the call
and the user's toggles allow; every call it makes is approved as the tool's policy says, runs, and comes back to it
once per iteration; at its limits it answers with what it has.
"""

import inspect
from contextlib import asynccontextmanager
from typing import Annotated, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ChatFeature,
    KnowledgeReference,
    KnowledgeSearchedEvent,
    LLMEvent,
    Message,
    RunToolLoopEvent,
    SearchKnowledgeEvent,
    ToolApprovalRequestEvent,
    ToolApprovalResponseEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolDefinition,
    ToolEvent,
    ToolLoopFinishedEvent,
    ToolLoopIterationEvent,
    ToolLoopMode,
    ToolLoopState,
    ToolResultEvent,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig
from swiss_ai_hub.core.topics import AgentInstanceTopic, PartialAgentTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge, answers_a_tool_call
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_fields import KnowledgeToolFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_source import KnowledgeToolSource
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_rule import ToolApprovalRule
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approvals import ToolApprovals
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop, every_call_answered
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.workflow.workflow_validation import WorkflowValidation

MODULE = "swiss_ai_hub.agent.capabilities.tool_loop.tool_loop"
T = LocaleHandler("en")
HISTORY = [ChatMessage(role=MessageRole.USER, content="What time is it, and how many vacation days do I get?")]


TOPIC = AgentInstanceTopic(
    agent_class="LoopAgent",
    agent_id="loop-test",
    thread_id="thread",
    display_id="display",
    run_id="run",
    event_type="control_event",
    event_name="ToolCallApprovedEvent",
    event_id="event",
)


class Toolbox(BaseToolSpec):
    spec_functions = ["echo", "broken", "draw", "code"]

    def __init__(self, context: ToolContext) -> None:
        self.context = context

    @ToolOptions.of(label=LocaleString(en="Echo"), approval_summary=LocaleString(en="Shout {text}"))
    async def echo(self, text: Annotated[str, "What to echo"]) -> str:
        """Echoes."""
        return f"{text.upper()} for {self.context.agent_config.agent_id}"

    async def broken(self, text: str) -> str:
        """Fails."""
        raise RuntimeError("tool down")

    @ToolOptions.of(chat_feature=ChatFeature.IMAGE_GENERATION)
    async def draw(self, text: str) -> str:
        """Draws."""
        return text

    @ToolOptions.of(default_approval=ToolApprovalPolicy.ONCE_PER_RUN, approve_every_call=True)
    async def code(self, text: str) -> str:
        """Runs code."""
        return text


ECHO = ToolDefinition(name="echo", description="Echoes.", parameters={"type": "object", "properties": {}})


class LoopAgent(Agent):
    tools = ToolLoop.over(Knowledge, Toolbox)


class _Context:
    def __init__(self, values: dict | None = None) -> None:
        self.values = dict(values or {})

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value


class _Config(KnowledgeToolFields, KnowledgeFields, ToolLoopFields, AgentConfig):
    pass


@pytest.fixture(autouse=True)
def _live_collections():
    with patch(
        "swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope.UserScopedRetrievers.namespaces_of",
        side_effect=lambda database: ["policies", "reports"] if database == "hr" else [],
    ):
        yield


def _sources(*namespaces: str) -> KnowledgeToolConfig:
    if not namespaces:
        return KnowledgeToolConfig()
    store = MilvusVectorStoreConfig(collection_name="hr", index_namespaces=list(namespaces))
    return KnowledgeToolConfig(sources=[KnowledgeToolSource(vector_store=store)])


def _config(collections: bool = True, **tool_loop: Any) -> _Config:
    return _Config(
        agent_id="loop-test",
        name=LocaleString(en="Loop"),
        description=LocaleString(en="Loop fixture"),
        knowledge_tool=_sources("policies") if collections else _sources(),
        tool_loop=ToolLoopConfig(**tool_loop),
    )


def _conversation(reply: Message) -> MagicMock:
    @asynccontextmanager
    async def cost_reporting_llm(*_args: Any, **_kwargs: Any):
        yield MagicMock(achat=AsyncMock(return_value=MagicMock(message=reply.to_llama_index())))

    conversation = MagicMock()
    conversation.llm.cost_reporting_llm = cost_reporting_llm
    conversation.llm.model_name = "text-generation/test"
    conversation.llm.token_counter = lambda text: text.split()
    conversation.input_budget.return_value = 100_000
    return conversation


def _displayer(reply: Message) -> MagicMock:
    turn = LLMEvent(input_messages=[], output_messages=[reply], chat_model_name="text-generation/test")
    return MagicMock(
        display_llm_stream=AsyncMock(return_value=turn), display_event=AsyncMock(), display_chunk=AsyncMock()
    )


def _state(mode: ToolLoopMode = ToolLoopMode.ANSWER, **update: Any) -> ToolLoopState:
    return ToolLoopState(
        messages=[Message.from_llama_index(message) for message in HISTORY],
        tools=[ECHO],
        mode=mode,
        **update,
    )


def _tool_call(call_id: str, name: str, arguments: str) -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def _calling(*calls: dict) -> Message:
    return Message(role="assistant", contents=[], tool_calls=list(calls))


ANSWER = Message.from_string(role="assistant", content="It is noon.")


async def _decide(
    state: ToolLoopState, reply: Message, run_context: "_Context | None" = None, **tool_loop: Any
) -> tuple[Any, MagicMock]:
    displayer = _displayer(reply)
    result = await ToolLoop.decide_step(
        LoopAgent(),
        iteration=ToolLoopIterationEvent(state=state),
        conversation=_conversation(reply),
        loop=_config(**tool_loop),
        run_context=run_context or _Context(),
        displayer=displayer,
        t=T,
    )
    return result, displayer


class TestOfferedTools:
    async def _start(self, requested: list[str], mode: ToolLoopMode = ToolLoopMode.ANSWER, **kwargs: Any) -> Any:
        request = LoopAgent.tools.run(HISTORY, mode=mode, tools=kwargs.pop("tools", None))
        config = kwargs.pop("config", _config(**kwargs))
        with patch(f"{MODULE}.RequestedFeatures.contains", new=AsyncMock(side_effect=lambda f, *_: f in requested)):
            with patch("swiss_ai_hub.core.generative_ai.KnowledgeCollectionLabel.of_reference", return_value="HR"):
                return await ToolLoop.start_step(
                    LoopAgent(),
                    request=request,
                    loop=config,
                    conversation=_conversation(ANSWER),
                    agent_config=config,
                    run_context=_Context(),
                    displayer=MagicMock(spec=EventDisplayer),
                    t=T,
                    topic=TOPIC,
                )

    @pytest.mark.asyncio
    async def test_the_declared_tools_are_offered_unless_their_toggle_is_off(self):
        event = await self._start(requested=[])

        assert [tool.name for tool in event.state.tools] == ["search_knowledge", "echo", "broken", "code"]

    @pytest.mark.asyncio
    async def test_a_toggled_tool_is_offered_once_the_user_switches_it_on(self):
        event = await self._start(requested=[ChatFeature.IMAGE_GENERATION])

        assert "draw" in [tool.name for tool in event.state.tools]

    @pytest.mark.asyncio
    async def test_the_profile_and_the_call_narrow_the_tools(self):
        event = await self._start(requested=[], disabled_tools=["broken"], tools=["echo", "broken"])

        assert [tool.name for tool in event.state.tools] == ["echo"]

    @pytest.mark.asyncio
    async def test_knowledge_is_offered_only_with_collections_to_search(self):
        event = await self._start(requested=[], config=_config(collections=False))

        assert "search_knowledge" not in [tool.name for tool in event.state.tools]

    @pytest.mark.asyncio
    async def test_gathering_with_nothing_to_offer_ends_without_a_model_call(self):
        event = await self._start(requested=[], mode=ToolLoopMode.GATHER, tools=[])

        assert isinstance(event, ToolLoopFinishedEvent)
        assert event.block == []


class TestDecisions:
    @pytest.mark.asyncio
    async def test_an_answer_ends_the_loop_with_the_streamed_reply(self):
        finished, displayer = await _decide(_state(), ANSWER)

        assert isinstance(finished, ToolLoopFinishedEvent)
        assert finished.answer.output_messages[-1].content == "It is noon."
        assert displayer.display_llm_stream.await_args.kwargs["tools"][0]["function"]["name"] == "echo"

    @pytest.mark.asyncio
    async def test_tool_calls_become_one_tool_event_each_and_a_join_point(self):
        reply = _calling(_tool_call("c1", "echo", '{"text": "a"}'), _tool_call("c2", "echo", '{"text": "b"}'))

        events, _ = await _decide(_state(), reply)

        decided, *calls = events
        assert isinstance(decided, ToolCallsDecidedEvent)
        assert decided.tool_call_ids == ["c1", "c2"]
        assert [(call.name, call.parameters) for call in calls] == [("echo", {"text": "a"}), ("echo", {"text": "b"})]
        assert all(isinstance(call, ToolEvent) for call in calls)
        assert decided.state.messages[-1].tool_calls == reply.tool_calls

    @pytest.mark.asyncio
    async def test_calls_beyond_the_run_budget_are_not_made(self):
        reply = _calling(_tool_call("c1", "echo", "{}"), _tool_call("c2", "echo", "{}"))

        events, _ = await _decide(_state(tool_calls_made=4), reply, max_tool_calls=5)

        assert events[0].tool_call_ids == ["c1"]

    @pytest.mark.asyncio
    async def test_at_the_limit_the_model_answers_without_tools(self):
        finished, displayer = await _decide(_state(iteration=5), ANSWER, max_iterations=5)

        assert finished.stopped_early
        assert displayer.display_llm_stream.await_args.kwargs["tools"] is None
        assert "Answer now" in displayer.display_llm_stream.await_args.args[2][-1].content

    @pytest.mark.asyncio
    async def test_gathering_at_the_limit_hands_back_what_it_has(self):
        gathered = [ChatMessage(role=MessageRole.SYSTEM, content="echo: A")]

        finished, displayer = await _decide(
            _state(ToolLoopMode.GATHER, iteration=1, max_iterations=1, gathered=gathered), ANSWER
        )

        assert (finished.block, finished.stopped_early) == (gathered, True)
        displayer.display_llm_stream.assert_not_awaited()
        assert displayer.display_event.await_args.args[0].done

    @pytest.mark.asyncio
    async def test_stopping_early_is_always_said_in_the_same_words(self):
        finished, displayer = await _decide(_state(iteration=5), ANSWER, max_iterations=5)

        notice = displayer.display_chunk.await_args.args[0]
        assert "reached its limit of tool calls" in notice
        assert finished.answer.output_messages[-1].content.endswith(notice)

    @pytest.mark.asyncio
    async def test_gathering_shows_that_it_is_deciding(self):
        _, displayer = await _decide(_state(ToolLoopMode.GATHER), ANSWER)

        statuses = [call.args[0] for call in displayer.display_event.await_args_list]
        assert [(status.description, status.done) for status in statuses] == [
            ("Deciding what to look up", False),
            ("Gathered what the answer needs", True),
        ]

    @pytest.mark.asyncio
    async def test_gathering_decides_silently(self):
        finished, displayer = await _decide(_state(ToolLoopMode.GATHER), ANSWER)

        assert finished.answer is None
        displayer.display_llm_stream.assert_not_awaited()


class TestApproval:
    async def _gate(
        self,
        name: str,
        run_context: _Context | None = None,
        parameters: dict[str, Any] | None = None,
        **tool_loop: Any,
    ) -> Any:
        return await ToolLoop.gate_step(
            LoopAgent(),
            call=ToolEvent(
                tool_call_id="c1", name=name, parameters={"text": "a"} if parameters is None else parameters
            ),
            loop=_config(**tool_loop),
            run_context=run_context or _Context(),
            thread_context=_Context(),
            t=T,
        )

    @pytest.mark.asyncio
    async def test_a_tool_without_a_policy_runs_straight_away(self):
        approved = await self._gate("echo")

        assert isinstance(approved, ToolCallApprovedEvent)
        assert (approved.kind, approved.arguments) == ("function", {"text": "a"})

    @pytest.mark.asyncio
    async def test_a_capability_tool_is_run_by_its_capability(self):
        approved = await self._gate("search_knowledge")

        assert approved.kind == "capability"

    @pytest.mark.asyncio
    async def test_a_tool_the_profile_guards_asks_the_user_first(self):
        rule = ToolApprovalRule(tool="echo", policy=ToolApprovalPolicy.ONCE_PER_THREAD)

        request = await self._gate("echo", approvals=[rule])

        assert isinstance(request, ToolApprovalRequestEvent)
        assert (request.hitl_type, request.tool_call_id, request.name) == ("confirmation", "c1", "echo")
        assert "Shout a" in request.question
        assert "Echo" in request.question

    @pytest.mark.asyncio
    async def test_a_tool_without_a_summary_is_asked_for_with_its_arguments_and_its_name_once(self):
        request = await self._gate("code")

        assert "- text: a" in request.question
        assert request.question.count("code") == 1

    @pytest.mark.asyncio
    async def test_a_call_without_arguments_or_summary_is_asked_for_plainly(self):
        request = await self._gate("code", parameters={})

        assert request.question == 'The assistant wants to use "code". Allow it?'

    @pytest.mark.asyncio
    async def test_an_approval_remembered_for_the_run_is_not_asked_again(self):
        rule = ToolApprovalRule(tool="echo", policy=ToolApprovalPolicy.ONCE_PER_RUN)
        run_context = _Context({"tool_loop:approved:echo": True})

        assert isinstance(await self._gate("echo", run_context, approvals=[rule]), ToolCallApprovedEvent)

    @pytest.mark.asyncio
    async def test_a_tool_approved_per_call_never_carries_an_approval_over(self):
        run_context = _Context({"tool_loop:approved:code": True})

        assert isinstance(await self._gate("code", run_context), ToolApprovalRequestEvent)

    @pytest.mark.asyncio
    async def test_an_unknown_tool_is_reported_to_the_model(self):
        result = await self._gate("nope")

        assert isinstance(result, ToolResultEvent)
        assert result.is_error

    async def _answer(self, approved: bool, policy: ToolApprovalPolicy) -> tuple[Any, _Context, _Context]:
        request = ToolApprovalRequestEvent(
            question="Allow?",
            topic=PartialAgentTopic(event_type="control_event", event_name="ToolApprovalResponseEvent"),
            tool_call_id="c1",
            name="echo",
            arguments={"text": "a"},
            kind="function",
        )
        run_context, thread_context = _Context(), _Context()
        result = await ToolLoop.approval_step(
            LoopAgent(),
            answer=ToolApprovalResponseEvent(response=approved, request_event=request),
            loop=_config(approvals=[ToolApprovalRule(tool="echo", policy=policy)]),
            run_context=run_context,
            thread_context=thread_context,
            t=T,
        )
        return result, run_context, thread_context

    @pytest.mark.asyncio
    async def test_a_declined_call_tells_the_model_to_answer_without_it(self):
        result, run_context, _ = await self._answer(False, ToolApprovalPolicy.ONCE_PER_RUN)

        assert isinstance(result, ToolResultEvent)
        assert result.is_error and "declined" in result.content
        assert run_context.values == {"tool_loop:declined:echo": True}

    @pytest.mark.asyncio
    async def test_a_declined_tool_is_not_offered_again_in_the_run(self):
        run_context = _Context({"tool_loop:declined:echo": True})

        _, displayer = await _decide(_state(), ANSWER, run_context=run_context)

        offered = [tool["function"]["name"] for tool in displayer.display_llm_stream.await_args.kwargs["tools"] or []]
        assert "echo" not in offered

    @pytest.mark.asyncio
    async def test_an_approved_call_runs_and_the_approval_is_remembered_as_the_policy_says(self):
        result, _, thread_context = await self._answer(True, ToolApprovalPolicy.ONCE_PER_THREAD)

        assert isinstance(result, ToolCallApprovedEvent)
        assert thread_context.values == {"tool_loop:approved:echo": True}

    def test_the_policy_defaults_to_the_tools_own(self):
        options = LoopAgent.tools.options("code")

        assert ToolApprovals.policy("code", options, ToolLoopConfig()) == ToolApprovalPolicy.EVERY_CALL


class TestFunctionTools:
    async def _run(self, name: str, arguments: dict) -> ToolResultEvent:
        return await ToolLoop.run_function_step(
            LoopAgent(),
            call=ToolCallApprovedEvent(tool_call_id="c1", name=name, arguments=arguments, kind="function"),
            request=RunToolLoopEvent(),
            agent_config=_config(),
            displayer=MagicMock(spec=EventDisplayer),
            t=T,
            topic=TOPIC,
        )

    def test_the_steps_building_a_tool_context_receive_the_run_topic(self):
        """The dispatcher injects a topic only into a parameter annotated exactly with a topic class."""
        for step_function in (ToolLoop.start_step, ToolLoop.run_function_step):
            assert inspect.signature(step_function).parameters["topic"].annotation is AgentInstanceTopic

    @pytest.mark.asyncio
    async def test_a_function_tool_returns_what_it_computed(self):
        result = await self._run("echo", {"text": "hi"})

        assert (result.content, result.is_error) == ("HI for loop-test", False)

    @pytest.mark.asyncio
    async def test_invalid_arguments_go_back_to_the_model(self):
        result = await self._run("echo", {})

        assert result.is_error and "Invalid arguments" in result.content

    @pytest.mark.asyncio
    async def test_a_failing_tool_does_not_end_the_run(self):
        result = await self._run("broken", {"text": "x"})

        assert result.is_error and "tool down" in result.content


class TestJoin:
    def _decided(self, iteration: int = 0) -> ToolCallsDecidedEvent:
        state = _state(ToolLoopMode.GATHER, iteration=iteration)
        return ToolCallsDecidedEvent(state=state, tool_call_ids=["c1", "c2"])

    def _result(self, call_id: str, content: str = "done", **fields: Any) -> ToolResultEvent:
        return ToolResultEvent(tool_call_id=call_id, name="echo", content=content, **fields)

    @pytest.mark.asyncio
    async def test_the_loop_waits_for_every_call_of_the_iteration(self):
        assert not await every_call_answered(self._decided(), [self._result("c1")], [])
        assert await every_call_answered(self._decided(), [self._result("c1"), self._result("c2")], [])

    @pytest.mark.asyncio
    async def test_an_iteration_is_joined_only_once(self):
        results = [self._result("c1"), self._result("c2")]
        next_iteration = ToolLoopIterationEvent(state=_state(iteration=1))

        assert not await every_call_answered(self._decided(), results, [next_iteration])

    @pytest.mark.asyncio
    async def test_another_loops_iterations_do_not_count_as_joined(self):
        results = [self._result("c1"), self._result("c2")]
        other_loop = ToolLoopIterationEvent(state=_state(iteration=3, loop="drafting"))

        assert await every_call_answered(self._decided(), results, [other_loop])

    @pytest.mark.asyncio
    async def test_results_go_back_to_the_model_and_into_the_gathered_context(self):
        block = [ChatMessage(role=MessageRole.SYSTEM, content="<REFERENCE_DOCUMENT id='s1'>…")]
        results = [self._result("c2", "second"), self._result("c1", "first", block=block), self._result("x")]

        event = await ToolLoop.join_step(
            LoopAgent(),
            decided=self._decided(),
            results=results,
            loop=_config(),
            conversation=_conversation(ANSWER),
        )

        state = event.state
        assert (state.iteration, state.tool_calls_made) == (1, 2)
        assert [(m.role, m.tool_call_id, m.content) for m in state.messages[-2:]] == [
            ("tool", "c1", "first"),
            ("tool", "c2", "second"),
        ]
        assert [message.content for message in state.gathered] == [block[0].content, "echo: second"]

    @pytest.mark.asyncio
    async def test_a_result_larger_than_its_room_is_cut(self):
        results = [self._result("c1", "word " * 500), self._result("c2")]

        event = await ToolLoop.join_step(
            LoopAgent(),
            decided=self._decided(),
            results=results,
            loop=_config(max_result_tokens=50),
            conversation=_conversation(ANSWER),
        )

        assert "cut to fit" in event.state.messages[-2].content
        assert len(event.state.messages[-2].content.split()) < 80


class TestKnowledgeAsATool:
    @pytest.mark.asyncio
    async def test_a_chosen_search_runs_the_regular_search_over_the_picked_collections(self):
        config = KnowledgeToolFields(knowledge_tool=_sources("policies", "reports"))
        call = ToolCallApprovedEvent(
            tool_call_id="c1",
            name="search_knowledge",
            arguments={"query": "vacation days", "collections": ["hr/policies"]},
            kind="capability",
        )

        request = await Knowledge.search_tool_call_step(LoopAgent(), call=call, request=RunToolLoopEvent(), tool=config)

        assert isinstance(request, SearchKnowledgeEvent)
        assert (request.query, request.tool_call_id) == ("vacation days", "c1")
        assert request.references == [KnowledgeReference(database="hr", namespace="policies")]

    @pytest.mark.asyncio
    async def test_what_the_search_found_goes_back_to_the_loop(self):
        block = [
            ChatMessage(role=MessageRole.SYSTEM, content="<REFERENCE_DOCUMENT id='s1'>25 days</REFERENCE_DOCUMENT>")
        ]
        searched = KnowledgeSearchedEvent(block=block, tool_call_id="c1")
        decided = ToolCallsDecidedEvent(state=_state(), tool_call_ids=["c1"])

        assert await answers_a_tool_call(searched, decided)
        result = await Knowledge.search_tool_result_step(LoopAgent(), searched=searched, decided=decided)

        assert (result.tool_call_id, result.block) == ("c1", block)
        assert "25 days" in result.content

    @pytest.mark.asyncio
    async def test_an_explicit_search_is_not_mistaken_for_a_tool_call(self):
        decided = ToolCallsDecidedEvent(state=_state(), tool_call_ids=["c1"])

        assert not await answers_a_tool_call(KnowledgeSearchedEvent(), decided)


class TestDeclaration:
    def test_tools_without_a_loop_are_refused(self):
        class ToolsButNoLoop(Agent):
            tools = ToolLoop.over(Toolbox)

        assert WorkflowValidation._tools_without_loop(ToolsButNoLoop)

    def test_offering_knowledge_as_a_tool_needs_its_tool_settings(self):
        class WithoutToolSettings(KnowledgeFields, ToolLoopFields, AgentConfig):
            pass

        problems = WorkflowValidation._missing_config_mixins(LoopAgent, WithoutToolSettings)

        assert any("Knowledge is offered as a tool" in problem for problem in problems)
        assert not WorkflowValidation._missing_config_mixins(LoopAgent, _Config)

    def test_a_capability_that_offers_no_tool_cannot_be_declared(self):
        with pytest.raises(ValueError, match="is no tool"):
            ToolLoop.over(Conversation)

    def test_tool_names_are_unique(self):
        with pytest.raises(ValueError, match="unique"):
            ToolLoop.over(Toolbox, Toolbox)

    def test_a_set_is_named_after_its_attribute(self):
        class TwoLoops(Agent):
            research = ToolLoop.over(Knowledge)
            drafting = ToolLoop.over(Toolbox)

        assert [tool_set.name for tool_set in TwoLoops.tool_sets()] == ["research", "drafting"]
        assert TwoLoops.research.run(HISTORY).loop == "research"
        assert TwoLoops.tool_set_offering("echo") is TwoLoops.drafting

    @pytest.mark.asyncio
    async def test_a_spec_method_is_offered_with_the_schema_of_its_signature(self):
        context = ToolContext(agent_config=_config(collections=False), displayer=MagicMock(spec=EventDisplayer), t=T)

        definitions = await LoopAgent.tools.definitions(context)

        echo = definitions["echo"]
        assert echo.parameters["properties"]["text"]["description"] == "What to echo"
        assert "Echoes." in echo.description

    def test_the_published_form_offers_the_blueprints_tools(self):
        published = ToolLoop.published_config(_config(), LoopAgent)

        assert [option["value"] for option in published.tool_loop.disabled_tools.options] == [
            "search_knowledge",
            "echo",
            "broken",
            "draw",
            "code",
        ]

    @pytest.mark.asyncio
    async def test_the_tool_call_carries_the_label_users_read(self):
        events, _ = await _decide(_state(), _calling(_tool_call("c1", "echo", '{"text": "a"}')))

        assert events[1].label == "Echo"
