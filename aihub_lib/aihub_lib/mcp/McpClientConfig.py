from typing import Annotated, Self

from pydantic import Field

from aihub_lib.agents.AgentConfig import StepConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import InputNumber, InputText, Password
from aihub_lib.nats.events.form.constraints import Gt


class McpClientConfig(StepConfig):
    """MCP connection configuration — injected as a StepConfig, used by the dispatcher to create a FastMCP Client."""

    name: Annotated[str | InputText, Field(description="Logical name for this connection.")]
    url: Annotated[str | InputText, Field(description="MCP server URL — FastMCP auto-infers the transport.")]
    api_key: Annotated[
        str | Password | None,
        Field(default=None, description="API key for authenticated MCP servers."),
    ]
    headers: Annotated[
        dict[str, str] | None,
        Field(default=None, description="Additional HTTP headers for the connection."),
    ]
    timeout: Annotated[
        float | InputNumber,
        Field(default=30.0, description="Client timeout in seconds."),
        Gt(0),
    ]

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            name=InputText(
                label=LocaleString.from_i18n_path("lib.mcp.config.name.label"),
                help=LocaleString.from_i18n_path("lib.mcp.config.name.help"),
            ),
            url=InputText(
                label=LocaleString.from_i18n_path("lib.mcp.config.url.label"),
                help=LocaleString.from_i18n_path("lib.mcp.config.url.help"),
            ),
            api_key=Password(
                label=LocaleString.from_i18n_path("lib.mcp.config.api_key.label"),
                help=LocaleString.from_i18n_path("lib.mcp.config.api_key.help"),
            ),
            timeout=InputNumber(
                label=LocaleString.from_i18n_path("lib.mcp.config.timeout.label"),
                help=LocaleString.from_i18n_path("lib.mcp.config.timeout.help"),
                min=1,
                max=300,
                step=1,
            ),
        )
