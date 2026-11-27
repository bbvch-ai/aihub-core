from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.settings import EnvironmentSettings


class ExternalAccessFilterSettings(EnvironmentSettings):
    """Deployment-level limits on the access resolvers a RAG agent profile may call."""

    model_config = EnvironmentSettings.create_settings_config("EXTERNAL_ACCESS_FILTER_")

    ALLOWED_PRIVATE_HOSTS: Annotated[
        str,
        Field(
            default="",
            description="Comma-separated host names a resolver URL may name although they are internal, such as a "
            "resolver reachable only on the company network. Every other internal host is refused, because an agent "
            "profile editor sets the URL, the API key travels with the request, and agents can reach the platform's "
            "own services.",
        ),
    ]

    def private_host_allow_list(self) -> frozenset[str]:
        return frozenset(host.strip().lower() for host in self.ALLOWED_PRIVATE_HOSTS.split(",") if host.strip())
