import logging
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    AgentInTheLoopRequestEvent,
    ToolCallApprovedEvent,
    ToolDefinition,
    ToolResultEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.agent_tools.agent_tool_arguments import AgentToolArguments
from swiss_ai_hub.agent.capabilities.agent_tools.agent_tool_fields import AgentToolFields
from swiss_ai_hub.agent.capabilities.agent_tools.offered_agents import OfferedAgents
from swiss_ai_hub.agent.capabilities.agent_tools.pending_agent_call import PendingAgentCall
from swiss_ai_hub.agent.capabilities.agent_tools.pending_agent_calls import PendingAgentCalls
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)

ASK_AGENT_TOOL = "ask_agent"
DESCRIPTION_LIMIT = 1024
DELEGATED_BY_KEY = "delegated_by"


@precondition()
async def asks_an_agent(call: ToolCallApprovedEvent) -> bool:
    return AgentTools.owns_tool(call.name) and call.name != ASK_AGENT_TOOL


@precondition()
async def answers_an_agent_call(
    outcome: AgentInTheLoop.response | AgentInTheLoop.exception | AgentInTheLoop.timeout, run_context: RunContext
) -> bool:
    return await PendingAgentCalls.find(outcome.request_event_id, run_context) is not None


class AgentTools(Capability):
    """
    Other agents the asking user may use, each offered to the model as a tool of its own (`ask_agent__{profile}`).

    The model calls one with a self-contained request; the agent runs with the asking user on a thread and display of
    its own through `AgentInTheLoop`, so its answer reaches the model as the tool result and only its steps reach the
    user, under the tool call. An agent that fails or misses the profile's deadline answers with an error, and the run
    continues. Which agents are offered is decided once per run (`OfferedAgents`): online, conversational, permitted
    to the asking user, admitted by the profile, never the asking agent itself, and none at the end of a chain of
    `max_depth` delegations.
    """

    calls: ClassVar[dict] = {}
    tool_name: ClassVar[str] = ASK_AGENT_TOOL
    tool_family: ClassVar[bool] = True
    tool_config: ClassVar[type[AgentToolFields]] = AgentToolFields
    tool_options: ClassVar[ToolOptions] = ToolOptions(
        label=AgentLocaleString.from_i18n_path("agent.agent_tools.tool.label")
    )

    @classmethod
    async def tool_definitions(cls, context: ToolContext) -> list[ToolDefinition]:
        config = getattr(context.agent_config, "agent_tools", None)
        if (
            config is None
            or context.access is None
            or context.callable_agents is None
            or context.run_context is None
            or await AgentTools._at_the_depth_limit(context.run_context, config.max_depth)
        ):
            return []
        chosen = OfferedAgents.choose(
            await context.callable_agents.online_agents(), config, context.access, context.topic, ASK_AGENT_TOOL
        )
        await OfferedAgents.keep([offered for offered, _ in chosen], context.run_context)
        return [
            ToolDefinition(
                name=offered.tool_name,
                description=AgentTools._description(agent.name, agent.description, context.t),
                parameters=AgentToolArguments.schema_for(context.t),
            )
            for offered, agent in chosen
        ]

    @classmethod
    async def member_options(cls, name: str, run_context: RunContext) -> ToolOptions:
        offered = await OfferedAgents.find(name, run_context)
        if offered is None:
            return cls.tool_options
        summary = AgentLocaleString.from_i18n_path("agent.agent_tools.tool.approval_summary")
        return ToolOptions(
            label=offered.name,
            approval_summary=LocaleString(
                **{
                    locale: summary.in_locale(locale).replace("{agent}", offered.name.in_locale(locale))
                    for locale in LocaleString.model_fields
                }
            ),
            default_approval=offered.approval,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.agent_tools.steps.ask_as_tool.name"),
        description=AgentLocaleString.from_i18n_path("agent.agent_tools.steps.ask_as_tool.description"),
        icon="mage:robot",
        precondition=asks_an_agent,
    )
    async def ask_agent_step(
        agent: Agent,
        call: ToolCallApprovedEvent,
        tool: AgentToolFields,
        run_context: RunContext,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> AgentInTheLoopRequestEvent | ToolResultEvent:
        """The model asked an agent it was offered: start that agent's run for the asking user."""
        offered = await OfferedAgents.find(call.name, run_context)
        if offered is None or user is None or tool.agent_tools is None:
            return AgentTools._error(call, t("agent.agent_tools.result.not_offered"))
        try:
            arguments = AgentToolArguments.model_validate(call.arguments)
        except ValidationError as error:
            return AgentTools._error(call, f"Invalid arguments: {error}")
        request = AgentInTheLoop.invoke(
            agent_class=offered.agent_class,
            agent_id=offered.agent_id,
            start_event=UserMessageEvent(
                user=user,
                locale=t.locale,
                messages=[ChatMessage(role=MessageRole.USER, content=arguments.message)],
            ),
            share_thread_id=False,
            share_display_id=False,
            timeout_seconds=tool.agent_tools.timeout_seconds,
            tool_call_id=call.tool_call_id,
        )
        await PendingAgentCalls.keep(
            request.event_id, PendingAgentCall(tool_call_id=call.tool_call_id, tool_name=call.name), run_context
        )
        logger.info(
            "[agent-tools] %s asks %s/%s for user %s in tenant %s",
            agent.__class__.__name__,
            offered.agent_class,
            offered.agent_id,
            user.id,
            user.acting_within_tenant.id if user.acting_within_tenant else None,
        )
        return request

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.agent_tools.steps.answer_tool_call.name"),
        description=AgentLocaleString.from_i18n_path("agent.agent_tools.steps.answer_tool_call.description"),
        icon="mage:robot",
        precondition=answers_an_agent_call,
    )
    async def agent_answered_step(
        agent: Agent,
        outcome: AgentInTheLoop.response | AgentInTheLoop.exception | AgentInTheLoop.timeout,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> ToolResultEvent:
        """Hand the agent's answer, failure or silence back to the model as the tool call's result."""
        call = await PendingAgentCalls.find(outcome.request_event_id, run_context)
        if outcome.is_aitl_response_event:
            stop = outcome.stop_event
            answer = stop.answer_text() or stop.model_dump_json(serialize_as_any=True)
            return ToolResultEvent(tool_call_id=call.tool_call_id, name=call.tool_name, content=answer)
        if outcome.is_in_the_loop_timeout_event:
            content = t("agent.agent_tools.result.no_answer", seconds=f"{outcome.timeout_seconds:g}")
        else:
            content = t("agent.agent_tools.result.failed", message=outcome.exception_event.message)
        return ToolResultEvent(tool_call_id=call.tool_call_id, name=call.tool_name, content=content, is_error=True)

    @staticmethod
    async def _at_the_depth_limit(run_context: RunContext, max_depth: int) -> bool:
        delegation = await run_context.get(DELEGATED_BY_KEY)
        return bool(delegation) and delegation["depth"] >= max_depth

    @staticmethod
    def _description(name: LocaleString, description: LocaleString, t: LocaleHandler) -> str:
        text = t(
            "agent.agent_tools.tool.description",
            agent=name.in_locale(t.locale),
            purpose=description.in_locale(t.locale),
        )
        return text[:DESCRIPTION_LIMIT]

    @staticmethod
    def _error(call: ToolCallApprovedEvent, content: str) -> ToolResultEvent:
        return ToolResultEvent(tool_call_id=call.tool_call_id, name=call.name, content=content, is_error=True)
