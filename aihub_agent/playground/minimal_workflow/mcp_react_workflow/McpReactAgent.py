import logging
from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpHostManager import McpHostManager
from aihub_lib.mcp.tool_calling import (
    build_tool_schemas,
    call_llm_with_tools,
    extract_mcp_result_text,
    parse_tool_calls,
    tool_result_message,
)
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.mcp_react_workflow.McpReactAgentConfig import McpReactAgentConfig

logger = logging.getLogger(__name__)


class McpReactAgent(Agent):
    """Demo agent with LLM-driven MCP tool calling (ReAct loop).

    Single-step bounded loop: LLM decides → execute MCP tools → repeat until done.
    """

    name: ClassVar[LocaleString] = LocaleString(
        en="MCP ReAct Agent",
        de="MCP ReAct Agent",
        fr="Agent MCP ReAct",
        it="Agente MCP ReAct",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Demo agent that uses LLM function calling to invoke MCP tools",
        de="Demo-Agent der LLM-Funktionsaufruf nutzt um MCP-Tools aufzurufen",
        fr="Agent démo qui utilise les appels de fonction LLM pour invoquer des outils MCP",
        it="Agente demo che usa le chiamate di funzione LLM per invocare strumenti MCP",
    )
    icon: ClassVar[str] = "mage:plug"

    @step()
    async def react_loop(
        self,
        event: UserMessageEvent,
        mcp_host: McpHostManager,
        config: McpReactAgentConfig,
    ) -> StopEvent:
        """ReAct loop: LLM picks tools, agent executes them, repeat until done."""
        mcp_tools = await mcp_host.list_all_tools()
        schemas, mcp_tool_names = build_tool_schemas(mcp_tools, [])
        messages: list[ChatMessage] = list(event.messages)

        for _ in range(config.mcp.max_tool_iterations):
            assistant_msg = await call_llm_with_tools(messages, schemas, config.llm)
            messages.append(assistant_msg)

            tool_calls = assistant_msg.additional_kwargs.get("tool_calls")
            if not tool_calls:
                break

            for call in parse_tool_calls(tool_calls, mcp_tool_names):
                try:
                    result = await mcp_host.call_tool(call.tool_name, call.arguments)
                    result_text = extract_mcp_result_text(result)
                except Exception:
                    result_text = f"Error: Tool '{call.tool_name}' execution failed"
                messages.append(tool_result_message(call.tool_call_id, call.tool_name, result_text))

        return StopEvent(result=messages[-1].content or "No response generated.")
