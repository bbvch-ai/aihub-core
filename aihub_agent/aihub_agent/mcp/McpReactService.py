import json
import logging
from typing import Any

from fastmcp import Client
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from mcp.types import Tool

from aihub_lib.displayers.EventDisplayer import EventDisplayer

logger = logging.getLogger(__name__)


class McpReactService:
    """Reusable MCP ReAct loop — LLM reasons about tools, calls them, iterates until a text answer."""

    @staticmethod
    def to_openai_tool_schemas(tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert MCP tools to OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                },
            }
            for tool in tools
        ]

    @staticmethod
    def extract_result_text(result: Any) -> str:
        """Extract text from MCP CallToolResult content blocks."""
        return " ".join(str(block.text) for block in result.content if hasattr(block, "text"))

    @staticmethod
    async def react_loop(
        mcp_client: Client,
        messages: list[ChatMessage],
        llm: LLM,
        displayer: EventDisplayer,
        model_name: str,
        max_iterations: int = 10,
    ) -> str:
        """Run the ReAct loop: LLM reasons, calls MCP tools, feeds results back, repeats until text answer."""
        tools = await mcp_client.list_tools()
        tool_schemas = McpReactService.to_openai_tool_schemas(tools)

        for _ in range(max_iterations):
            response = await llm.achat(messages, tools=tool_schemas)
            assistant_msg = response.message
            tool_calls = assistant_msg.additional_kwargs.get("tool_calls", [])

            if not tool_calls:
                content = str(assistant_msg.content)
                await displayer.display_chunk(content, model_name)
                return content

            messages.append(assistant_msg)

            for tc in tool_calls:
                tool_name = tc.function.name
                raw_args = tc.function.arguments
                arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                await displayer.display_thought(f"Calling tool: {tool_name}({json.dumps(arguments)})")
                result = await mcp_client.call_tool(tool_name, arguments)
                result_text = McpReactService.extract_result_text(result)

                messages.append(
                    ChatMessage(
                        role=MessageRole.TOOL,
                        content=result_text,
                        additional_kwargs={"tool_call_id": tc.id, "name": tool_name},
                    )
                )

        response = await llm.achat(messages)
        content = str(response.message.content)
        await displayer.display_chunk(content, model_name)
        return content
