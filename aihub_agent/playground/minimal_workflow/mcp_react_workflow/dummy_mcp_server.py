"""Minimal MCP server for testing the MCP React agent. Run this before trigger.py."""

import datetime

from fastmcp import FastMCP

mcp = FastMCP("test-tools")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().isoformat()


@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9090)
