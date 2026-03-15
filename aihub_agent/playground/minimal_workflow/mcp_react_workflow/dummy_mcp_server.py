"""Minimal MCP server for testing the MCP React agent. Run this before trigger.py."""

from fastmcp import FastMCP

mcp = FastMCP("test-tools")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9090)
