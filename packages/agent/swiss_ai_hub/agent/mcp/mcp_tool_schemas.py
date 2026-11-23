import json
import logging
from typing import Any

from fastmcp import Client
from mcp.shared.exceptions import McpError
from mcp.types import TextContent as McpTextContent
from mcp.types import Tool
from swiss_ai_hub.core.events.agent.semantic.llm.message import Message, TextContent
from swiss_ai_hub.core.events.agent.semantic.tool.tool_event import ToolEvent
from swiss_ai_hub.core.mcp import McpClientConfig

from swiss_ai_hub.agent.mcp.mcp_call_span import RESOURCES_READ_METHOD, TOOLS_CALL_METHOD, McpCallSpan
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
    server: McpClientConfig,
    tool_call_id: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> Message:
    """Execute a single MCP tool call or resource read, traced as a tool, and return the response Message.

    A call the server refuses (an unknown tool, invalid arguments, a failing tool) goes back to the model as an error
    result, as the tool loop does, so the model can correct itself; an unreachable server still fails the step."""
    is_resource_read = tool_name == READ_MCP_RESOURCE_TOOL_NAME
    method = RESOURCES_READ_METHOD if is_resource_read else TOOLS_CALL_METHOD
    with McpCallSpan.open(server, method, tool_name, arguments) as span:
        try:
            result_text, is_error = await _call(mcp_client, tool_name, arguments, is_resource_read)
        except McpError as error:
            result_text, is_error = str(error), True
        if is_error:
            logger.warning("MCP tool %s returned an error: %s", tool_name, result_text)
            result_text = f"Error: {result_text}"
        McpCallSpan.close(span, result_text, is_error)

    return Message(
        role="tool",
        tool_call_id=tool_call_id,
        name=tool_name,
        contents=[TextContent(text=result_text)],
    )


async def _call(
    mcp_client: Client, tool_name: str, arguments: dict[str, Any], is_resource_read: bool
) -> tuple[str, bool]:
    """The call's text and whether the server reported it as failed."""
    if is_resource_read:
        return await execute_resource_read(mcp_client, arguments["uri"]), False
    result = await mcp_client.call_tool(tool_name, arguments, raise_on_error=False)
    return " ".join(block.text for block in result.content if isinstance(block, McpTextContent)), result.is_error
