from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.mcp.mcp_client_factory import McpClientFactory
    from swiss_ai_hub.agent.mcp.mcp_resource_schemas import (
        execute_resource_read,
        fetch_static_resources,
        resource_read_tool_schema,
    )
    from swiss_ai_hub.agent.mcp.mcp_tool_schemas import (
        execute_single_tool_call,
        to_openai_tool_schemas,
        to_tool_events,
    )

__all__ = [
    "McpClientFactory",
    "execute_resource_read",
    "execute_single_tool_call",
    "fetch_static_resources",
    "resource_read_tool_schema",
    "to_openai_tool_schemas",
    "to_tool_events",
]

_MCP_RESOURCE_SCHEMAS_MODULE = "swiss_ai_hub.agent.mcp.mcp_resource_schemas"
_MCP_TOOL_SCHEMAS_MODULE = "swiss_ai_hub.agent.mcp.mcp_tool_schemas"

_LAZY_IMPORTS = {
    "McpClientFactory": "swiss_ai_hub.agent.mcp.mcp_client_factory",
    "execute_resource_read": _MCP_RESOURCE_SCHEMAS_MODULE,
    "fetch_static_resources": _MCP_RESOURCE_SCHEMAS_MODULE,
    "resource_read_tool_schema": _MCP_RESOURCE_SCHEMAS_MODULE,
    "execute_single_tool_call": _MCP_TOOL_SCHEMAS_MODULE,
    "to_openai_tool_schemas": _MCP_TOOL_SCHEMAS_MODULE,
    "to_tool_events": _MCP_TOOL_SCHEMAS_MODULE,
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
