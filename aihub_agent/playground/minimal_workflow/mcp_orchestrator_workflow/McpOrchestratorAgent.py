import logging
from typing import Any, ClassVar

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpHostManager import McpHostManager
from aihub_lib.mcp.tool_calling import (
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
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.mcp_orchestrator_workflow.events.ToolResultEvent import ToolResultEvent
from playground.minimal_workflow.mcp_orchestrator_workflow.McpOrchestratorAgentConfig import (
    McpOrchestratorAgentConfig,
)

logger = logging.getLogger(__name__)

TOOL_SCHEMAS = "tool_schemas"
MCP_TOOL_NAMES = "mcp_tool_names"
ACTIVE_CALL = "active_call"
USER = "user"


class McpOrchestratorAgent(Agent):
    """Demo agent combining MCP tool calling with agent delegation.

    Demonstrates how to use Agent-in-the-Loop (AITL) for delegating to sub-agents while
    also calling MCP tools directly. MCP tools execute inline, agent delegation goes through AITL.
    """

    name: ClassVar[LocaleString] = LocaleString(
        en="MCP Orchestrator Agent",
        de="MCP Orchestrator Agent",
        fr="Agent Orchestrateur MCP",
        it="Agente Orchestratore MCP",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent that combines MCP tool calling with agent delegation in a unified ReAct loop",
        de="Agent der MCP-Tool-Aufrufe mit Agent-Delegierung in einer einheitlichen ReAct-Schleife kombiniert",
        fr="Agent combinant l'appel d'outils MCP avec la délégation d'agents dans une boucle ReAct unifiée",
        it="Agente che combina chiamate MCP con delega ad altri agenti in un loop ReAct unificato",
    )
    icon: ClassVar[str] = "mage:network"

    @step(max_executions_per_run=15)
    async def plan_step(
        self,
        event: UserMessageEvent | ToolResultEvent,
        mcp_host: McpHostManager,
        config: McpOrchestratorAgentConfig,
        run_context: RunContext,
    ) -> ToolResultEvent | StopEvent | AgentInTheLoop.request:
        """LLM planning step — call LLM, execute MCP tools inline, or delegate to agents."""
        if isinstance(event, UserMessageEvent):
            mcp_tools = await mcp_host.list_all_tools()
            agent_schemas = [
                agent_tool_schema(a.tool_name, a.tool_description, a.tool_parameters_schema)
                for a in config.delegated_agents
            ]
            schemas, mcp_tool_names = build_tool_schemas(mcp_tools, agent_schemas)
            await run_context.set(TOOL_SCHEMAS, schemas)
            await run_context.set(MCP_TOOL_NAMES, list(mcp_tool_names))
            await run_context.set(USER, event.user.model_dump())
            messages: list[ChatMessage] = list(event.messages)
        else:
            messages = [ChatMessage(**m) for m in await run_context.get("messages", [])]
            if event.tool_call_id:
                messages.append(tool_result_message(event.tool_call_id, event.tool_name, event.result_text))

        schemas = await run_context.get(TOOL_SCHEMAS, [])
        assistant_msg = await call_llm_with_tools(messages, schemas, config.llm)
        messages.append(assistant_msg)

        tool_calls = assistant_msg.additional_kwargs.get("tool_calls")
        if not tool_calls:
            return StopEvent(result=assistant_msg.content or "No response generated.")

        mcp_tool_names = set(await run_context.get(MCP_TOOL_NAMES, []))
        parsed = parse_tool_calls(tool_calls, mcp_tool_names)

        # Execute all MCP tool calls inline
        for call in parsed:
            if not call.is_mcp:
                continue
            try:
                result = await mcp_host.call_tool(call.tool_name, call.arguments)
                result_text = extract_mcp_result_text(result)
            except Exception:
                result_text = f"Error: Tool '{call.tool_name}' execution failed"
            messages.append(tool_result_message(call.tool_call_id, call.tool_name, result_text))

        # Find first agent delegation
        agent_call = next((c for c in parsed if not c.is_mcp), None)
        if not agent_call:
            # Only MCP calls — results already in messages, loop back for next LLM turn
            await run_context.set("messages", [m.model_dump() for m in messages])
            return ToolResultEvent(tool_call_id="", tool_name="", result_text="")

        agent_tool = next((a for a in config.delegated_agents if a.tool_name == agent_call.tool_name), None)
        if not agent_tool:
            messages.append(tool_result_message(agent_call.tool_call_id, agent_call.tool_name, "Error: Unknown agent"))
            await run_context.set("messages", [m.model_dump() for m in messages])
            return ToolResultEvent(
                tool_call_id=agent_call.tool_call_id,
                tool_name=agent_call.tool_name,
                result_text="Error: Unknown agent",
            )

        await run_context.set("messages", [m.model_dump() for m in messages])
        await run_context.set(ACTIVE_CALL, agent_call.model_dump())

        user = UserIdentity(**await run_context.get(USER, {}))
        query = agent_call.arguments.get("query", str(agent_call.arguments))
        return AgentInTheLoop.invoke(
            agent_id=agent_tool.agent_id,
            agent_class=agent_tool.agent_class,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=user,
            ),
        )

    @step()
    async def handle_agent_response(
        self, response: AgentInTheLoop.response, run_context: RunContext
    ) -> ToolResultEvent:
        """Handle successful response from a delegated agent."""
        active: dict[str, Any] = await run_context.get(ACTIVE_CALL, {})
        result = str(getattr(response.stop_event, "result", ""))
        return ToolResultEvent(tool_call_id=active["tool_call_id"], tool_name=active["tool_name"], result_text=result)

    @step()
    async def handle_agent_exception(
        self, response: AgentInTheLoop.exception, run_context: RunContext
    ) -> ToolResultEvent:
        """Handle exception from a delegated agent."""
        active: dict[str, Any] = await run_context.get(ACTIVE_CALL, {})
        error = f"Error: Agent delegation failed: {response.exception_event}"
        return ToolResultEvent(tool_call_id=active["tool_call_id"], tool_name=active["tool_name"], result_text=error)
