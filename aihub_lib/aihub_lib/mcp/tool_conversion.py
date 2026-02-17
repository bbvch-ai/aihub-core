from typing import Any

from mcp.types import Tool


def mcp_tool_to_openai_function(tool: Tool) -> dict[str, Any]:
    """Convert an MCP tool schema to the OpenAI function calling format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
        },
    }
