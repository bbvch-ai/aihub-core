import asyncio
import json
import logging
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    LLMEvent,
    Message,
    RunToolLoopEvent,
    TextContent,
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
from swiss_ai_hub.core.generative_ai import estimate_prompt_tokens
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures
from swiss_ai_hub.agent.capabilities.tool_loop.declared_tool import DeclaredTool
from swiss_ai_hub.agent.capabilities.tool_loop.function_tool import FunctionTool
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approvals import ToolApprovals
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)

CITE_SOURCES_KEY = "tool_loop:cite_sources"


@precondition()
async def runs_in_the_loop(call: ToolCallApprovedEvent) -> bool:
    return call.kind == "function"


@precondition()
async def every_call_answered(
    decided: ToolCallsDecidedEvent, results: list[ToolResultEvent], iterations: list[ToolLoopIterationEvent]
) -> bool:
    """Joins once per iteration: the calls are all answered and no later iteration has started from them yet."""
    answered = {result.tool_call_id for result in results}
    already_joined = any(iteration.state.iteration > decided.state.iteration for iteration in iterations)
    return not already_joined and set(decided.tool_call_ids) <= answered


class ToolLoop(Capability):
    """
    The model decides which of the blueprint's tools to use, runs them and decides again, until it is done:

    - `run(history, mode)` is answered with `ToolLoopFinishedEvent`. In `ANSWER` mode it carries the model's reply,
      for `Conversation.complete(...)`; in `GATHER` mode the tool results as a context block, for
      `Conversation.compose(...)` and the blueprint's own answer.

    A blueprint declares the tools it may offer with `tools = ToolLoop.over(...)`: capabilities that offer a tool,
    whose calls run their own sub-workflow with the same events as an explicit call, and function tools, which run
    here. The profile and the chat toggles the user switched on narrow them per message; with no tool left the
    model answers directly. Every decision, call, approval and result is an event, so the loop is as visible in the
    trace and the chat as a fixed flow.
    """

    calls: ClassVar[dict] = {RunToolLoopEvent: (ToolLoopFinishedEvent,)}
    required_config: ClassVar[type[ToolLoopFields]] = ToolLoopFields

    RunRequest = RunToolLoopEvent
    Finished = ToolLoopFinishedEvent

    @staticmethod
    def over(*tools: FunctionTool | type[Capability]) -> tuple[DeclaredTool, ...]:
        declared = tuple(DeclaredTool.of(tool) for tool in tools)
        names = [tool.name for tool in declared]
        if len(names) != len(set(names)):
            msg = f"Tool names must be unique within a blueprint, got {names}"
            raise ValueError(msg)
        return declared

    @staticmethod
    def names(tools: tuple[DeclaredTool, ...]) -> list[str]:
        return [tool.name for tool in tools]

    @staticmethod
    def run(
        history: list[ChatMessage],
        mode: ToolLoopMode = ToolLoopMode.ANSWER,
        cite_sources: bool = True,
        tools: list[str] | None = None,
    ) -> RunToolLoopEvent:
        return RunToolLoopEvent(history=history, mode=mode, cite_sources=cite_sources, tools=tools)

    @staticmethod
    def route(history: list[ChatMessage], cite_sources: bool = True) -> RunToolLoopEvent:
        """One decision: the model picks the tools worth running now, and their results come back as context."""
        return RunToolLoopEvent(history=history, mode=ToolLoopMode.GATHER, cite_sources=cite_sources, max_iterations=1)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.start.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.start.description"),
        icon="mdi:toolbox-outline",
    )
    async def start_step(
        agent: Agent,
        request: RunToolLoopEvent,
        loop: ToolLoopFields,
        agent_config: AgentConfig,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> ToolLoopIterationEvent | ToolLoopFinishedEvent:
        """Work out which tools are on offer for this message; gathering with nothing to offer ends right away."""
        offered = await ToolLoop._offered(agent, request, loop, agent_config, run_context, t)
        if not offered and request.mode == ToolLoopMode.GATHER:
            return ToolLoopFinishedEvent()
        await run_context.set(CITE_SOURCES_KEY, request.cite_sources)
        return ToolLoopIterationEvent(
            state=ToolLoopState(
                messages=[Message.from_llama_index(message) for message in request.history],
                tools=offered,
                mode=request.mode,
                max_iterations=request.max_iterations,
                cite_sources=request.cite_sources,
            )
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.decide.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.decide.description"),
        icon="mage:light-bulb",
    )
    async def decide_step(
        agent: Agent,
        iteration: ToolLoopIterationEvent,
        conversation: ConversationFields,
        loop: ToolLoopFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[ToolCallsDecidedEvent | ToolEvent] | ToolLoopFinishedEvent:
        """Ask the model to answer or to call tools; at the loop's limits it must answer with what it has."""
        state = iteration.state
        exhausted = ToolLoop._exhausted(state, loop)
        if exhausted and state.mode == ToolLoopMode.GATHER:
            return ToolLoopFinishedEvent(block=state.gathered, stopped_early=True)

        messages = [message.to_llama_index() for message in state.messages]
        if exhausted:
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=t("agent.tool_loop.prompt.limit_reached")))
        tools = [tool.to_openai() for tool in state.tools] if state.tools and not exhausted else None
        turn = await ToolLoop._turn(messages, tools, state.mode, conversation, displayer, user)

        assistant = turn.output_messages[-1]
        if not assistant.tool_calls:
            answer = turn if state.mode == ToolLoopMode.ANSWER else None
            return ToolLoopFinishedEvent(answer=answer, block=state.gathered, stopped_early=exhausted)

        remaining = loop.tool_loop.max_tool_calls - state.tool_calls_made
        assistant = assistant.model_copy(update={"tool_calls": assistant.tool_calls[:remaining]})
        calls = [ToolLoop._tool_event(tool_call, state.tools) for tool_call in assistant.tool_calls]
        decided = ToolCallsDecidedEvent(
            state=state.model_copy(update={"messages": [*state.messages, assistant]}),
            tool_call_ids=[call.tool_call_id for call in calls],
        )
        return [decided, *calls]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.gate.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.gate.description"),
        icon="mdi:shield-check-outline",
    )
    async def gate_step(
        agent: Agent,
        call: ToolEvent,
        loop: ToolLoopFields,
        run_context: RunContext,
        thread_context: ThreadContext,
        t: LocaleHandler,
    ) -> ToolCallApprovedEvent | ToolApprovalRequestEvent | ToolResultEvent:
        """Let the call through, or ask the user first when the tool's approval policy says so."""
        tool = ToolLoop._declared(agent, call.name)
        if tool is None:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id,
                name=call.name or "",
                content=t("agent.tool_loop.prompt.unknown_tool", tool=call.name),
                is_error=True,
            )
        cite_sources = await run_context.get(CITE_SOURCES_KEY, True)
        if await ToolApprovals.needs_approval(tool, loop.tool_loop, run_context, thread_context):
            return ToolApprovalRequestEvent(
                question=t(
                    "agent.tool_loop.approval.question",
                    tool=tool.name,
                    arguments=json.dumps(call.parameters or {}, ensure_ascii=False),
                ),
                topic=PartialAgentTopic(
                    event_type=AgentTopicManager.CONTROL_EVENT,
                    event_name=ToolApprovalResponseEvent.event_name_from_class(),
                ),
                tool_call_id=call.tool_call_id,
                name=tool.name,
                arguments=call.parameters or {},
                kind=tool.kind,
                cite_sources=cite_sources,
            )
        return ToolCallApprovedEvent(
            tool_call_id=call.tool_call_id,
            name=tool.name,
            arguments=call.parameters or {},
            kind=tool.kind,
            cite_sources=cite_sources,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.approval.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.approval.description"),
        icon="mage:user-check",
    )
    async def approval_step(
        agent: Agent,
        answer: ToolApprovalResponseEvent,
        loop: ToolLoopFields,
        run_context: RunContext,
        thread_context: ThreadContext,
        t: LocaleHandler,
    ) -> ToolCallApprovedEvent | ToolResultEvent:
        """Run an approved call, remembering the approval as the policy allows; tell the model about a declined one."""
        request = answer.request_event
        if not answer.response:
            return ToolResultEvent(
                tool_call_id=request.tool_call_id,
                name=request.name,
                content=t("agent.tool_loop.prompt.declined", tool=request.name),
                is_error=True,
            )
        tool = ToolLoop._declared(agent, request.name)
        await ToolApprovals.remember(tool, loop.tool_loop, run_context, thread_context)
        return ToolCallApprovedEvent(
            tool_call_id=request.tool_call_id,
            name=request.name,
            arguments=request.arguments,
            kind=tool.kind,
            cite_sources=request.cite_sources,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.run_function.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.run_function.description"),
        icon="mage:wand",
        precondition=runs_in_the_loop,
    )
    async def run_function_step(
        agent: Agent,
        call: ToolCallApprovedEvent,
        agent_config: AgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        access: AccessChecker | None = None,
    ) -> ToolResultEvent:
        """Run a function tool; a failure goes back to the model as an error result rather than ending the run."""
        tool = ToolLoop._declared(agent, call.name).function
        context = ToolContext(agent_config=agent_config, displayer=displayer, t=t, user=user, access=access)
        try:
            content = await tool.run(tool.arguments.model_validate(call.arguments), context)
        except ValidationError as error:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Invalid arguments: {error}", is_error=True
            )
        except Exception as error:
            logger.exception("[tool-loop] Tool %s failed", call.name)
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Error: {error}", is_error=True
            )
        return ToolResultEvent(tool_call_id=call.tool_call_id, name=call.name, content=content)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.join.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.join.description"),
        icon="mdi:call-merge",
        precondition=every_call_answered,
    )
    async def join_step(
        agent: Agent,
        decided: ToolCallsDecidedEvent,
        results: list[ToolResultEvent],
        loop: ToolLoopFields,
        conversation: ConversationFields,
    ) -> ToolLoopIterationEvent:
        """Hand every result of the iteration back to the model, each cut to fit the room left in the prompt."""
        by_id = {result.tool_call_id: result for result in results}
        answered = [by_id[tool_call_id] for tool_call_id in decided.tool_call_ids]
        state = decided.state
        room = ToolLoop._room_per_result(state, len(answered), loop, conversation)
        counter = conversation.llm.token_counter
        tool_messages = [
            Message(
                role="tool",
                tool_call_id=result.tool_call_id,
                name=result.name,
                contents=[TextContent(text=ToolLoop._cut(result.content, room, counter))],
            )
            for result in answered
        ]
        gathered = [
            *state.gathered,
            *(
                message
                for result in answered
                if not result.is_error
                for message in (
                    result.block or [ChatMessage(role=MessageRole.SYSTEM, content=f"{result.name}: {result.content}")]
                )
            ),
        ]
        return ToolLoopIterationEvent(
            state=state.model_copy(
                update={
                    "messages": [*state.messages, *tool_messages],
                    "iteration": state.iteration + 1,
                    "tool_calls_made": state.tool_calls_made + len(answered),
                    "gathered": gathered,
                }
            )
        )

    @staticmethod
    async def _offered(
        agent: Agent,
        request: RunToolLoopEvent,
        loop: ToolLoopFields,
        agent_config: AgentConfig,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> list[ToolDefinition]:
        """The blueprint's tools, less those the profile disables, the call excludes or whose toggle is off."""
        blueprint = type(agent)
        offered = []
        for tool in blueprint.tools:
            if tool.name in loop.tool_loop.disabled_tools or (
                request.tools is not None and tool.name not in request.tools
            ):
                continue
            if tool.chat_feature and not await RequestedFeatures.contains(tool.chat_feature, run_context, blueprint):
                continue
            definition = await asyncio.to_thread(tool.definition, agent_config, t.locale)
            if definition is not None:
                offered.append(definition)
        return offered

    @staticmethod
    def _declared(agent: Agent, name: str | None) -> DeclaredTool | None:
        return next((tool for tool in type(agent).tools if tool.name == name), None)

    @staticmethod
    def _exhausted(state: ToolLoopState, loop: ToolLoopFields) -> bool:
        max_iterations = min(loop.tool_loop.max_iterations, state.max_iterations or loop.tool_loop.max_iterations)
        return state.iteration >= max_iterations or state.tool_calls_made >= loop.tool_loop.max_tool_calls

    @staticmethod
    async def _turn(
        messages: list[ChatMessage],
        tools: list[dict] | None,
        mode: ToolLoopMode,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        user: UserIdentity | None,
    ) -> LLMEvent:
        """The model's turn: streamed when it may be the reply, silent when the loop only gathers."""
        async with conversation.llm.cost_reporting_llm(displayer, user=user) as llm:
            if mode == ToolLoopMode.ANSWER:
                return await displayer.display_llm_stream(conversation.llm, llm, messages, tools=tools)
            response = await (llm.achat(messages, tools=tools) if tools else llm.achat(messages))
        return LLMEvent(
            input_messages=[Message.from_llama_index(message) for message in messages],
            output_messages=[Message.from_llama_index(response.message)],
            chat_model_name=conversation.llm.model_name,
        )

    @staticmethod
    def _tool_event(tool_call: dict, offered: list[ToolDefinition]) -> ToolEvent:
        function = tool_call["function"]
        raw_arguments = function.get("arguments") or {}
        try:
            arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        except json.JSONDecodeError:
            arguments = {}
        definition = next((tool for tool in offered if tool.name == function["name"]), None)
        return ToolEvent(
            tool_call_id=tool_call["id"],
            name=function["name"],
            description=definition.description if definition else None,
            json_schema=definition.parameters if definition else None,
            parameters=arguments if isinstance(arguments, dict) else {},
        )

    @staticmethod
    def _room_per_result(
        state: ToolLoopState, count: int, loop: ToolLoopFields, conversation: ConversationFields
    ) -> int:
        """Each result's share of the room left in the prompt, never more than the profile's cap."""
        used = estimate_prompt_tokens(
            [message.to_llama_index() for message in state.messages], conversation.llm.token_counter
        )
        left = max(conversation.input_budget() - used, 0)
        return min(loop.tool_loop.max_result_tokens, left // max(count, 1))

    @staticmethod
    def _cut(content: str, room: int, counter) -> str:
        tokens = len(counter(content))
        if tokens <= room:
            return content
        return content[: max(int(len(content) * room / tokens), 0)] + "\n[…cut to fit the context]"
