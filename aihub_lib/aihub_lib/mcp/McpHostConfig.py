from typing import Annotated, Literal

from pydantic import BaseModel, Field, SecretStr

from aihub_lib.agents.AgentConfig import StepConfig


class McpConnectionConfig(BaseModel):
    """Configuration for a single MCP Client-Server connection (1:1 per MCP spec)."""

    name: Annotated[str, Field(description="Logical name for this connection.")]
    url: Annotated[str, Field(description="MetaMCP endpoint or direct MCP server URL.")]
    transport: Annotated[
        Literal["streamable_http", "sse"],
        Field(default="streamable_http", description="MCP transport protocol."),
    ]
    api_key: Annotated[
        SecretStr | None,
        Field(default=None, description="API key for MetaMCP or authenticated servers."),
    ]
    headers: Annotated[
        dict[str, str] | None,
        Field(default=None, description="Additional HTTP headers for the connection."),
    ]


class McpHostConfig(StepConfig):
    """MCP Host configuration for agents.

    The agent acts as an MCP Host, managing one Client per connection.
    Each connection is a 1:1 Client-Server pair as per MCP spec.
    """

    connections: Annotated[
        list[McpConnectionConfig],
        Field(min_length=1, description="List of MCP server connections."),
    ]
    max_tool_iterations: Annotated[
        int,
        Field(default=10, ge=1, le=50, description="Maximum tool-use loop iterations."),
    ]
