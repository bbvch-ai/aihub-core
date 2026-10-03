import json
import logging
from typing import Any, ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
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
    ToolLoopStatusEvent,
    ToolResultEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approvals import ToolApprovals
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_condenser import ToolLoopCondenser
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.capabilities.tool_loop.tool_set import ToolSet
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)

CITE_SOURCES_KEY = "tool_loop:cite_sources"
DECLINED_KEY = "tool_loop:declined:{tool}"


@precondition()
async def runs_in_the_loop(call: ToolCallApprovedEvent) -> bool:
    return call.kind == "function"


@precondition()
async def fits_the_prompt(iteration: ToolLoopIterationEvent) -> bool:
    return not iteration.state.needs_condensing


@precondition()
async def outgrew_the_prompt(iteration: ToolLoopIterationEvent) -> bool:
    return iteration.state.needs_condensing


@precondition()
async def every_call_answered(
    decided: ToolCallsDecidedEvent, results: list[ToolResultEvent], iterations: list[ToolLoopIterationEvent]
) -> bool:
    """Joins once per iteration: the calls are all answered and no later iteration of the loop started from them."""
    answered = {result.tool_call_id for result in results}
    already_joined = any(
        iteration.state.loop == decided.state.loop and iteration.state.iteration > decided.state.iteration
        for iteration in iterations
    )
    return not already_joined and set(decided.tool_call_ids) <= answered


class ToolLoop(Capability):
    """
    The model decides which tools of one of the blueprint's tool sets to use, runs them and decides again, until it
    is done:

    - `tools.run(history, mode)` on a set declared with `tools = ToolLoop.over(...)` is answered with
      `ToolLoopFinishedEvent`. In `ANSWER` mode it carries the model's reply, for `Conversation.complete(...)`; in
      `GATHER` mode the tool results as a context block, for `Conversation.compose(...)` and the blueprint's own
      answer. `tools.route(history)` is one gathering decision.

    Capability tools run their capability's own sub-workflow, with the same events as an explicit call; LlamaIndex
    tools and tool specs run here. The profile and the chat toggles the user switched on narrow a set per message,
    and gathering with nothing left ends without a model call. Every decision, approval, call and result is an
    event, and each carries the loop's name, so a blueprint may run several of its sets one after another.
    """

    calls: ClassVar[dict] = {RunToolLoopEvent: (ToolLoopFinishedEvent,)}
    required_config: ClassVar[type[ToolLoopFields]] = ToolLoopFields

    RunRequest = RunToolLoopEvent
    Finished = ToolLoopFinishedEvent

    @staticmethod
    def over(*tools: Any) -> ToolSet:
        return ToolSet.of(tools)

    @classmethod
    def published_config[TConfig: AgentConfig](cls, config: TConfig, blueprint: type[Agent]) -> TConfig:
        """The loop's form offers the blueprint's own tools, which only the blueprint knows."""
        if not isinstance(config, ToolLoopFields):
            return config
        names = list(dict.fromkeys(name for tool_set in blueprint.tool_sets() for name in tool_set.names()))
        return config.model_copy(update={"tool_loop": ToolLoopConfig.as_form(names)})

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
        conversation: ConversationFields,
        agent_config: AgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        access: AccessChecker | None = None,
    ) -> ToolLoopIterationEvent | ToolLoopFinishedEvent:
        """Work out which tools are on offer for this message; gathering with nothing to offer ends right away."""
        context = ToolLoop._context(request, agent_config, displayer, t, user, access)
        offered = await ToolLoop._offered(agent, request, loop, context, run_context)
        if not offered and request.mode == ToolLoopMode.GATHER:
            return ToolLoopFinishedEvent(loop=request.loop)
        await run_context.set(CITE_SOURCES_KEY, request.cite_sources)
        messages = [Message.from_llama_index(message) for message in request.history]
        return ToolLoopIterationEvent(
            state=ToolLoopState(
                loop=request.loop,
                messages=messages,
                tools=offered,
                mode=request.mode,
                max_iterations=request.max_iterations,
                cite_sources=request.cite_sources,
                needs_condensing=ToolLoopCondenser.outgrown(
                    messages, offered, conversation.input_budget(), conversation.llm.token_counter
                ),
            )
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.decide.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.decide.description"),
        icon="mage:light-bulb",
        precondition=fits_the_prompt,
    )
    async def decide_step(
        agent: Agent,
        iteration: ToolLoopIterationEvent,
        conversation: ConversationFields,
        loop: ToolLoopFields,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[ToolCallsDecidedEvent | ToolEvent] | ToolLoopFinishedEvent:
        """Ask the model to answer or to call tools; at the loop's limits it must answer with what it has.

        A tool the user declined is no longer offered in this run, since models ask for it again regardless of being
        told not to, and the user would be prompted until they gave in. Offered no tools, for whatever reason, the
        model sees the earlier tool turns as plain text and is told to answer now.
        """
        state = iteration.state
        exhausted = ToolLoop._exhausted(state, loop)
        if state.mode == ToolLoopMode.GATHER:
            await ToolLoop._status(displayer, state, t, "stopped_early" if exhausted else "deciding", done=exhausted)
            if exhausted:
                return ToolLoopFinishedEvent(loop=state.loop, block=state.gathered, stopped_early=True)

        available = [
            tool for tool in state.tools if not await run_context.get(DECLINED_KEY.format(tool=tool.name), False)
        ]
        tools = [tool.to_openai() for tool in available] if available and not exhausted else None
        history = ToolLoop._tool_turns_as_text(state.messages) if tools is None else state.messages
        messages = [message.to_llama_index() for message in history]
        if tools is None:
            # A user turn: chat templates such as Qwen's reject any system message after the first. Without it, a
            # model told by its instructions to use tools calls one anyway, and the gateway strips the call to nothing.
            note = "limit_reached" if exhausted else "no_tools"
            messages.append(ChatMessage(role=MessageRole.USER, content=t(f"agent.tool_loop.prompt.{note}")))
        turn = await ToolLoop._turn(messages, tools, state.mode, conversation, displayer, user)

        assistant = turn.output_messages[-1]
        if not assistant.tool_calls:
            return await ToolLoop._finish(state, turn, exhausted, displayer, t)

        remaining = loop.tool_loop.max_tool_calls - state.tool_calls_made
        assistant = assistant.model_copy(update={"tool_calls": assistant.tool_calls[:remaining]})
        tool_set = type(agent).tool_set(state.loop)
        calls = [ToolLoop._tool_event(call, state.tools, tool_set, t) for call in assistant.tool_calls]
        decided = ToolCallsDecidedEvent(
            state=state.model_copy(update={"messages": [*state.messages, assistant]}),
            tool_call_ids=[call.tool_call_id for call in calls],
        )
        return [decided, *calls]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.condense.name"),
        description=AgentLocaleString.from_i18n_path("agent.tool_loop.steps.condense.description"),
        icon="mdi:arrow-collapse-vertical",
        precondition=outgrew_the_prompt,
    )
    async def condense_step(
        agent: Agent,
        iteration: ToolLoopIterationEvent,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> ToolLoopIterationEvent:
        """Condense the loop's conversation to fit the prompt again before the model decides on it."""
        condenser = ToolLoopCondenser(conversation.task_llm, conversation.input_budget(), displayer, t, user)
        return ToolLoopIterationEvent(state=await condenser.condense(iteration.state))

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
        tool_set = type(agent).tool_set_offering(call.name)
        # Only an offered tool carries its schema; a disabled, toggled-off or other set's tool must not run.
        if tool_set is None or call.json_schema is None:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id,
                name=call.name or "",
                content=t("agent.tool_loop.prompt.unknown_tool", tool=call.name),
                is_error=True,
            )
        options = tool_set.options(call.name)
        cite_sources = await run_context.get(CITE_SOURCES_KEY, True)
        arguments = call.parameters or {}
        if await ToolApprovals.needs_approval(call.name, options, loop.tool_loop, run_context, thread_context):
            summary = options.summary_in(arguments, t.locale)
            return ToolApprovalRequestEvent(
                question=t(
                    "agent.tool_loop.approval.question" if summary else "agent.tool_loop.approval.question_plain",
                    tool=options.label_in(call.name, t.locale),
                    summary=summary,
                ),
                topic=PartialAgentTopic(
                    event_type=AgentTopicManager.CONTROL_EVENT,
                    event_name=ToolApprovalResponseEvent.event_name_from_class(),
                ),
                tool_call_id=call.tool_call_id,
                name=call.name,
                arguments=arguments,
                kind=tool_set.kind(call.name),
                cite_sources=cite_sources,
            )
        return ToolCallApprovedEvent(
            tool_call_id=call.tool_call_id,
            name=call.name,
            arguments=arguments,
            kind=tool_set.kind(call.name),
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
            await run_context.set(DECLINED_KEY.format(tool=request.name), True)
            return ToolResultEvent(
                tool_call_id=request.tool_call_id,
                name=request.name,
                content=t("agent.tool_loop.prompt.declined", tool=request.name),
                is_error=True,
            )
        tool_set = type(agent).tool_set_offering(request.name)
        await ToolApprovals.remember(
            request.name, tool_set.options(request.name), loop.tool_loop, run_context, thread_context
        )
        return ToolCallApprovedEvent(
            tool_call_id=request.tool_call_id,
            name=request.name,
            arguments=request.arguments,
            kind=tool_set.kind(request.name),
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
        request: RunToolLoopEvent,
        agent_config: AgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        access: AccessChecker | None = None,
    ) -> ToolResultEvent:
        """Run a LlamaIndex tool; a failure goes back to the model as an error result rather than ending the run."""
        context = ToolLoop._context(request, agent_config, displayer, t, user, access)
        tool = type(agent).tool_set_offering(call.name).function_tools(context)[call.name]
        try:
            output = await tool.acall(**call.arguments)
        except TypeError as error:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Invalid arguments: {error}", is_error=True
            )
        except Exception as error:
            logger.exception("[tool-loop] Tool %s failed", call.name)
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Error: {error}", is_error=True
            )
        return ToolResultEvent(
            tool_call_id=call.tool_call_id,
            name=call.name,
            content=str(output.content),
            is_error=bool(getattr(output, "is_error", False)),
        )

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
        """Hand every result of the iteration back to the model, each within the profile's cap; a conversation that
        outgrew the prompt is condensed before the model decides again."""
        by_id = {result.tool_call_id: result for result in results}
        answered = [by_id[tool_call_id] for tool_call_id in decided.tool_call_ids]
        state = decided.state
        room = loop.tool_loop.max_result_tokens
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
        messages = [*state.messages, *tool_messages]
        return ToolLoopIterationEvent(
            state=state.model_copy(
                update={
                    "messages": messages,
                    "iteration": state.iteration + 1,
                    "tool_calls_made": state.tool_calls_made + len(answered),
                    "gathered": gathered,
                    "needs_condensing": ToolLoopCondenser.outgrown(
                        messages, state.tools, conversation.input_budget(), counter
                    ),
                }
            )
        )

    @staticmethod
    async def _offered(
        agent: Agent, request: RunToolLoopEvent, loop: ToolLoopFields, context: ToolContext, run_context: RunContext
    ) -> list[ToolDefinition]:
        """The set's tools, less those the profile disables, the call excludes or whose toggle is off."""
        blueprint = type(agent)
        tool_set = blueprint.tool_set(request.loop)
        definitions = await tool_set.definitions(context)
        offered = []
        for name, definition in definitions.items():
            if name in loop.tool_loop.disabled_tools or (request.tools is not None and name not in request.tools):
                continue
            feature = tool_set.options(name).chat_feature
            if feature and not await RequestedFeatures.contains(feature, run_context, blueprint):
                continue
            offered.append(definition)
        return offered

    @staticmethod
    def _context(
        request: RunToolLoopEvent,
        agent_config: AgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None,
        access: AccessChecker | None,
    ) -> ToolContext:
        return ToolContext(
            agent_config=agent_config,
            displayer=displayer,
            t=t,
            user=user,
            access=access,
            files=request.files,
            knowledge_references=request.knowledge_references,
        )

    @staticmethod
    async def _finish(
        state: ToolLoopState, turn: LLMEvent, exhausted: bool, displayer: EventDisplayer, t: LocaleHandler
    ) -> ToolLoopFinishedEvent:
        """The model is done. Stopping at the limits is always said in the same words, not left to the model."""
        if state.mode == ToolLoopMode.GATHER:
            await ToolLoop._status(displayer, state, t, "gathered", done=True)
            return ToolLoopFinishedEvent(loop=state.loop, block=state.gathered, stopped_early=exhausted)
        if exhausted:
            notice = f"\n\n_{t('agent.tool_loop.notice.stopped_early')}_"
            await displayer.display_chunk(notice, turn.chat_model_name)
            reply = turn.output_messages[-1]
            turn = turn.model_copy(
                update={
                    "output_messages": [
                        *turn.output_messages[:-1],
                        Message.from_string(
                            role="assistant", content=(reply.content or "") + notice, name=turn.chat_model_name
                        ),
                    ]
                }
            )
        return ToolLoopFinishedEvent(loop=state.loop, answer=turn, stopped_early=exhausted)

    @staticmethod
    async def _status(
        displayer: EventDisplayer, state: ToolLoopState, t: LocaleHandler, phase: str, done: bool
    ) -> None:
        await displayer.display_event(
            ToolLoopStatusEvent(loop=state.loop, description=t(f"agent.tool_loop.status.{phase}"), done=done)
        )

    @staticmethod
    def _tool_turns_as_text(messages: list[Message]) -> list[Message]:
        """The loop's calls and results as one plain assistant turn, for an answer offered no tools.

        Offered no tools after a tool-call history, Gemma answers with nothing at all; in plain text it answers.
        """
        kept: list[Message] = []
        notes: list[str] = []
        for message in messages:
            if message.role == "tool":
                notes.append(f"{message.name}:\n{message.content}")
            elif message.tool_calls:
                notes.extend([message.content] if message.content else [])
            else:
                kept.extend([Message.from_string(role="assistant", content="\n\n".join(notes))] if notes else [])
                notes = []
                kept.append(message)
        kept.extend([Message.from_string(role="assistant", content="\n\n".join(notes))] if notes else [])
        return kept

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
    def _tool_event(tool_call: dict, offered: list[ToolDefinition], tool_set: ToolSet, t: LocaleHandler) -> ToolEvent:
        function = tool_call["function"]
        raw_arguments = function.get("arguments") or {}
        try:
            arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        except json.JSONDecodeError:
            arguments = {}
        name = function["name"]
        definition = next((tool for tool in offered if tool.name == name), None)
        return ToolEvent(
            tool_call_id=tool_call["id"],
            name=name,
            label=tool_set.options(name).label_in(name, t.locale) if tool_set.kind(name) else name,
            description=definition.description if definition else None,
            json_schema=definition.parameters if definition else None,
            parameters=arguments if isinstance(arguments, dict) else {},
        )

    @staticmethod
    def _cut(content: str, room: int, counter) -> str:
        tokens = len(counter(content))
        if tokens <= room:
            return content
        return content[: max(int(len(content) * room / tokens), 0)] + "\n[…cut to fit the context]"
