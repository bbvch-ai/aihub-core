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
