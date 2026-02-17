from typing import Any, ClassVar

from aihub_lib.mcp.McpHostManager import McpHostManager
from aihub_lib.mcp.tool_calling import (
    ParsedToolCall,
    agent_tool_schema,
    build_tool_schemas,
    call_llm_with_tools,
    extract_mcp_result_text,
    parse_tool_calls,
    tool_result_message,
)
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from aihub_lib.nats.events.agent_in_the_loop.AgentInTheLoop import AgentInTheLoop
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.McpOrchestratorAgent.configs.McpOrchestratorAgentConfig import (
    McpOrchestratorAgentConfig,
)
from aihub_agent.agents.McpOrchestratorAgent.events.ActiveDelegationEvent import ActiveDelegationEvent
from aihub_agent.agents.McpOrchestratorAgent.events.PlanEvent import PlanEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.i18n.AgentLocaleString import AgentLocaleString
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step

TOOL_SCHEMAS = "tool_schemas"
MCP_TOOL_NAMES = "mcp_tool_names"


@precondition()
async def delegation_context_ready(delegation: ActiveDelegationEvent | None) -> bool:
    """Ensure delegation context is available before handling agent response or exception."""
    return delegation is not None


class McpOrchestratorAgent(Agent):
    """MCP Host agent that combines MCP tool calling with agent delegation in a unified ReAct loop.

    Four steps, each does one thing. Tool schemas in RunContext (constant). Conversation state
    flows through PlanEvent. Agent delegation state flows through ActiveDelegationEvent.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.mcp_orchestrator_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:network"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.initialize.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.initialize.description"),
        icon="mage:brain",
    )
    async def init_step(
        self,
        event: UserMessageEvent,
        mcp_host: McpHostManager,
        run_context: RunContext,
        agent_config: McpOrchestratorAgentConfig,
    ) -> PlanEvent:
        """Discover MCP tools, build schemas, and initialize conversation."""
        mcp_tools = await mcp_host.list_all_tools()
        agent_schemas = [
            agent_tool_schema(a.tool_name, a.tool_description, a.tool_parameters_schema)
            for a in agent_config.delegated_agents
        ]
        schemas, mcp_tool_names = build_tool_schemas(mcp_tools, agent_schemas)
        await run_context.set(TOOL_SCHEMAS, schemas)
        await run_context.set(MCP_TOOL_NAMES, list(mcp_tool_names))

        messages = list(event.messages)
        if agent_config.system_prompt:
            messages.insert(0, ChatMessage(role=MessageRole.SYSTEM, content=agent_config.system_prompt.resolve()))

        return PlanEvent(messages=messages, user=event.user)

    @step(
        max_executions_per_run=15,
        name=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.plan.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.plan.description"),
        icon="mage:brain",
    )
    async def plan_step(
        self,
        event: PlanEvent,
        run_context: RunContext,
        mcp_host: McpHostManager,
        agent_config: McpOrchestratorAgentConfig,
    ) -> PlanEvent | StopEvent | list[AgentInTheLoop.request | ActiveDelegationEvent]:
        """Call LLM with conversation + tools, execute MCP tools, or delegate to agents."""
        messages = list(event.messages)
        pending = list(event.pending_calls)

        if pending:
            call = ParsedToolCall(**pending.pop(0))

            if call.is_mcp:
                try:
                    result = await mcp_host.call_tool(call.tool_name, call.arguments)
                    result_text = extract_mcp_result_text(result)
                except Exception:
                    result_text = f"Error: Tool '{call.tool_name}' execution failed"
                messages.append(tool_result_message(call.tool_call_id, call.tool_name, result_text))
                return PlanEvent(messages=messages, pending_calls=pending, user=event.user)

            agent_tool = next((a for a in agent_config.delegated_agents if a.tool_name == call.tool_name), None)
            if not agent_tool:
                messages.append(tool_result_message(call.tool_call_id, call.tool_name, "Error: Unknown agent tool"))
                return PlanEvent(messages=messages, pending_calls=pending, user=event.user)

            query = call.arguments.get("query", str(call.arguments))
            return [
                AgentInTheLoop.invoke(
                    agent_id=agent_tool.agent_id,
                    agent_class=agent_tool.agent_class,
                    start_event=UserMessageEvent(
                        messages=[ChatMessage(content=query, role=MessageRole.USER)],
                        user=event.user,
                    ),
                ),
                ActiveDelegationEvent(
                    tool_call_id=call.tool_call_id,
                    tool_name=call.tool_name,
                    messages=messages,
                    pending_calls=pending,
                    user=event.user,
                ),
            ]

        schemas: list[dict[str, Any]] = await run_context.get(TOOL_SCHEMAS, [])
        assistant_msg = await call_llm_with_tools(messages, schemas, agent_config.llm)
        messages.append(assistant_msg)

        tool_calls = assistant_msg.additional_kwargs.get("tool_calls")
        if not tool_calls:
            return StopEvent(result=assistant_msg.content or "No response generated.")

        mcp_tool_names = set(await run_context.get(MCP_TOOL_NAMES, []))
        pending = [c.model_dump() for c in parse_tool_calls(tool_calls, mcp_tool_names)]

        return PlanEvent(messages=messages, pending_calls=pending, user=event.user)

    @step(
        precondition=delegation_context_ready,
        name=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.agent_response.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.agent_response.description"),
        icon="mage:check-circle",
    )
    async def handle_agent_response(
        self,
        response: AgentInTheLoop.response,
        delegation: ActiveDelegationEvent,
    ) -> PlanEvent:
        """Convert delegated agent result to tool result, emit PlanEvent."""
        result = str(getattr(response.stop_event, "result", ""))
        messages = list(delegation.messages)
        messages.append(tool_result_message(delegation.tool_call_id, delegation.tool_name, result))
        return PlanEvent(messages=messages, pending_calls=delegation.pending_calls, user=delegation.user)

    @step(
        precondition=delegation_context_ready,
        name=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.agent_exception.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.steps.agent_exception.description"),
        icon="mage:warning",
    )
    async def handle_agent_exception(
        self,
        response: AgentInTheLoop.exception,
        delegation: ActiveDelegationEvent,
    ) -> PlanEvent:
        """Handle delegated agent error, append error to conversation, emit PlanEvent."""
        error_text = f"Error: Agent delegation failed: {response.exception_event}"
        messages = list(delegation.messages)
        messages.append(tool_result_message(delegation.tool_call_id, delegation.tool_name, error_text))
        return PlanEvent(messages=messages, pending_calls=delegation.pending_calls, user=delegation.user)
