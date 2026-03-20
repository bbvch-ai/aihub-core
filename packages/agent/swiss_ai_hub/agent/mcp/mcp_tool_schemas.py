import json
import logging
from typing import Any

from fastmcp import Client
from mcp.types import TextContent as McpTextContent
from mcp.types import Tool
from swiss_ai_hub.core.events.agent.semantic.llm.message import Message, TextContent
from swiss_ai_hub.core.events.agent.semantic.tool.tool_event import ToolEvent

from swiss_ai_hub.agent.mcp.mcp_resource_schemas import READ_MCP_RESOURCE_TOOL_NAME, execute_resource_read

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


def to_tool_events(
    tool_calls: list[dict[str, Any]],
    tool_schemas: list[dict[str, Any]],
) -> list[ToolEvent]:
    """Convert OpenAI-format tool calls into ToolEvents for workflow dispatch."""
    tool_events: list[ToolEvent] = []
    for tool_call in tool_calls:
        function = tool_call["function"]
        tool_name = function["name"]
        arguments = (
            json.loads(function["arguments"]) if isinstance(function["arguments"], str) else function["arguments"]
        )
        tool_description = next(
            (t["function"]["description"] for t in tool_schemas if t["function"]["name"] == tool_name),
            None,
        )
        tool_events.append(
            ToolEvent(
                tool_call_id=tool_call["id"],
                name=tool_name,
                description=tool_description,
                parameters=arguments,
            )
        )
    return tool_events


async def execute_single_tool_call(
    mcp_client: Client,
    tool_call_id: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> Message:
    """Execute a single MCP tool call or resource read and return the response Message."""
    if tool_name == READ_MCP_RESOURCE_TOOL_NAME:
        result_text = await execute_resource_read(mcp_client, arguments["uri"])
    else:
        result = await mcp_client.call_tool(tool_name, arguments)
        result_text = " ".join(block.text for block in result.content if isinstance(block, McpTextContent))

        if result.is_error:
            logger.warning("MCP tool %s returned an error: %s", tool_name, result_text)
            result_text = f"Error: {result_text}"

    return Message(
        role="tool",
        tool_call_id=tool_call_id,
        name=tool_name,
        contents=[TextContent(text=result_text)],
    )
