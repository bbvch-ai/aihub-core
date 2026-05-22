from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.elements.select_button import SelectButton
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class McpClientConfig(StepConfig):
    """MCP connection configuration — injected as a StepConfig, used by the dispatcher to create a FastMCP Client."""

    name: Annotated[str | InputText, Field(description="Logical name for this connection.")]
    url: Annotated[str | InputText, Field(description="MCP server URL — FastMCP auto-infers the transport.")]
    auth_mode: Annotated[
        Literal["none", "api_key", "user_token"] | SelectButton,
        Field(
            default="api_key",
            description=(
                "How to authenticate to the MCP server: no credentials, a static API key, "
                "or the requesting user's forwarded token."
            ),
        ),
    ]
    api_key: Annotated[
        str | Password,
        Field(default="", description="Static API key — used only when auth_mode is 'api_key'."),
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
            auth_mode=SelectButton(
                label=LocaleString.from_i18n_path("lib.mcp.config.auth_mode.label"),
                help=LocaleString.from_i18n_path("lib.mcp.config.auth_mode.help"),
                options=[
                    {
                        "label": LocaleString.from_i18n_path("lib.mcp.config.auth_mode.none_label"),
                        "value": "none",
                    },
                    {
                        "label": LocaleString.from_i18n_path("lib.mcp.config.auth_mode.api_key_label"),
                        "value": "api_key",
                    },
                    {
                        "label": LocaleString.from_i18n_path("lib.mcp.config.auth_mode.user_token_label"),
                        "value": "user_token",
                    },
                ],
                option_label="label",
                option_value="value",
                ref="mcp_auth_mode",
            ),
            api_key=Password(
                label=LocaleString.from_i18n_path("lib.mcp.config.api_key.label"),
                help=LocaleString.from_i18n_path("lib.mcp.config.api_key.help"),
                condition_if="$get(mcp_auth_mode).value === 'api_key'",
            ),
            timeout=InputNumber(
                label=LocaleString.from_i18n_path("lib.mcp.config.timeout.label"),
                help=LocaleString.from_i18n_path("lib.mcp.config.timeout.help"),
                min=1,
                max=300,
                step=1,
            ),
        )
