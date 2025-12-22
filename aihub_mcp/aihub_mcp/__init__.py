"""
aihub_mcp - Full-featured MCP server for Swiss AI Hub.

This package bridges the Swiss AI Agent Protocol (SAAP) with the Model Context Protocol (MCP),
enabling external clients like Claude Code, Cursor, and VS Code extensions to interact with
AI Hub agents as first-class MCP tools.

Key features:
- Dynamic agent discovery and MCP tool registration
- Human-in-the-loop via MCP elicitation
- LLM sampling from MCP client
- Progress streaming for agent thoughts and outputs
- Streamable HTTP and SSE transports
"""

__version__ = "0.1.0"


# Lazy imports to avoid circular dependencies
def __getattr__(name: str) -> object:
    if name == "MCPServer":
        from aihub_mcp.server.MCPServer import MCPServer

        return MCPServer
    if name == "MCPSettings":
        from aihub_mcp.settings.MCPSettings import MCPSettings

        return MCPSettings
    if name == "MCPRunner":
        from aihub_mcp.runners.MCPRunner import MCPRunner

        return MCPRunner
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["MCPServer", "MCPSettings", "MCPRunner"]
