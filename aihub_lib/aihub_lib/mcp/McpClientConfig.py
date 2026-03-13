from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.agents.AgentConfig import StepConfig


class McpClientConfig(StepConfig):
    """MCP connection configuration — injected as a StepConfig, used by the dispatcher to create a FastMCP Client."""

    name: Annotated[str, Field(description="Logical name for this connection.")]
    url: Annotated[str, Field(description="MCP server URL — FastMCP auto-infers the transport.")]
    api_key: Annotated[
        SecretStr | None,
        Field(default=None, description="API key for authenticated MCP servers."),
    ]
    headers: Annotated[
        dict[str, str] | None,
        Field(default=None, description="Additional HTTP headers for the connection."),
    ]
    timeout: Annotated[
        float,
        Field(default=30.0, gt=0, description="Client timeout in seconds."),
    ]
