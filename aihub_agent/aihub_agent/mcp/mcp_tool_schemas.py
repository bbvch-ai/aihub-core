import json
import logging
from typing import Any

from aihub_lib.nats.events.semantic.llm.Message import Message, TextContent
from fastmcp import Client
from mcp.types import TextContent as McpTextContent
from mcp.types import Tool

logger = logging.getLogger(__name__)


def to_openai_tool_schemas(tools: list[Tool]) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to OpenAI function-calling format for LLM consumption."""
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


async def execute_tool_calls(mcp_client: Client, tool_calls: list[dict[str, Any]]) -> list[Message]:
    """Execute tool calls on an MCP server and return tool response Messages."""
    messages: list[Message] = []

    for tool_call in tool_calls:
        function = tool_call["function"]
        tool_name = function["name"]
        arguments = (
            json.loads(function["arguments"]) if isinstance(function["arguments"], str) else function["arguments"]
        )

        result = await mcp_client.call_tool(tool_name, arguments)
        result_text = " ".join(block.text for block in result.content if isinstance(block, McpTextContent))

        if result.is_error:
            logger.warning("MCP tool %s returned an error: %s", tool_name, result_text)
            result_text = f"Error: {result_text}"

        messages.append(
            Message(
                role="tool",
                tool_call_id=tool_call["id"],
                name=tool_name,
                contents=[TextContent(text=result_text)],
            )
        )

    return messages
