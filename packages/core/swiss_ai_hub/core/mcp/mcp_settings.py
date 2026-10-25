from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class McpSettings(EnvironmentSettings):
    """Deployment-level limits on the MCP servers an agent profile may connect to."""

    model_config = EnvironmentSettings.create_settings_config("MCP_")

    ALLOWED_PRIVATE_HOSTS: Annotated[
        str,
        Field(
            default="",
            description="Comma-separated host names an MCP server URL may name although they are internal, such as "
            "the platform's own API (`api`) or an MCP server reachable only on the company network. Every other "
            "internal host is refused, because an agent profile editor sets the URL and agents can reach the "
            "platform's own services.",
        ),
    ]

    def private_host_allow_list(self) -> frozenset[str]:
        return frozenset(host.strip().lower() for host in self.ALLOWED_PRIVATE_HOSTS.split(",") if host.strip())
