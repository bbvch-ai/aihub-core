import json
import logging
from typing import Any, ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from fastmcp import Client
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from mcp.types import Tool

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.mcp_react_workflow.McpReactAgentConfig import McpReactAgentConfig

logger = logging.getLogger(__name__)


class McpReactAgent(Agent):
    """ReAct agent — LLM reasons about which MCP tools to call, executes them, and iterates until it has an answer."""

    name: ClassVar[LocaleString] = LocaleString(
        en="MCP React Agent", de="MCP React Agent", fr="Agent MCP React", it="Agente MCP React"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Calls tools on external MCP servers",
        de="Ruft Tools auf externen MCP-Servern auf",
        fr="Appelle des outils sur des serveurs MCP externes",
        it="Chiama strumenti su server MCP esterni",
    )
    icon: ClassVar[str] = "mage:plug"

    @step()
    async def react_step(
        self,
        event: UserMessageEvent,
        mcp_client: Client,
        config: McpReactAgentConfig,
        displayer: EventDisplayer,
    ) -> StopEvent:
        """Run the ReAct loop: LLM reasons → calls tools → feeds results back → repeats until text answer."""
        tools = await mcp_client.list_tools()
        tool_schemas = [McpReactAgent._to_openai_schema(t) for t in tools]

        messages = list(event.messages)

        async with config.llm.cost_reporting_llm(displayer) as llm:
            for _ in range(config.max_iterations):
                response = await llm.achat(messages, tools=tool_schemas)
                assistant_msg = response.message
                tool_calls = assistant_msg.additional_kwargs.get("tool_calls", [])

                if not tool_calls:
                    await displayer.display_chunk(str(assistant_msg.content), config.llm.model_name)
                    return StopEvent()

                messages.append(assistant_msg)

                for tc in tool_calls:
                    tool_name = tc.function.name
                    raw_args = tc.function.arguments
                    arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                    await displayer.display_thought(f"Calling tool: {tool_name}({json.dumps(arguments)})")
                    result = await mcp_client.call_tool(tool_name, arguments)
                    result_text = McpReactAgent._extract_result_text(result)

                    messages.append(
                        ChatMessage(
                            role=MessageRole.TOOL,
                            content=result_text,
                            additional_kwargs={"tool_call_id": tc.id, "name": tool_name},
                        )
                    )

            # Max iterations reached — force a final text response without tools
            response = await llm.achat(messages)
            await displayer.display_chunk(str(response.message.content), config.llm.model_name)
            return StopEvent()

    @staticmethod
    def _to_openai_schema(tool: Tool) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema or {"type": "object", "properties": {}},
            },
        }

    @staticmethod
    def _extract_result_text(result: Any) -> str:
        return " ".join(str(block.text) for block in result.content if hasattr(block, "text"))
