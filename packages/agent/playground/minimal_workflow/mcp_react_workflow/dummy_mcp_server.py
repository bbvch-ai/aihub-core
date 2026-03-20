"""Minimal MCP server for testing the MCP React agent. Run this before trigger.py."""

from fastmcp import FastMCP

mcp = FastMCP("test-tools")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.resource("config://system")
def system_config() -> str:
    """System configuration and version info."""
    return "System version: 1.0, Environment: test, Max retries: 3"


@mcp.resource("users://{user_id}/profile")
def user_profile(user_id: str) -> str:
    """Look up a user profile by ID."""
    return f"Profile for user {user_id}: name=Test User, role=admin, active=true"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9090)
