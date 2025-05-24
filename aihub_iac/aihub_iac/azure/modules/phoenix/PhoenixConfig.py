from typing import ClassVar

from pydantic import Field

from aihub_iac.azure.resources.BaseConfig import BaseConfig
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class PhoenixConfig(BaseConfig):
    """Configuration class for API service infrastructure"""

    _registry_settings: ClassVar[RegistrySettings] = RegistrySettings()
    _postgres_settings: ClassVar[PostgresAuthSettings] = PostgresAuthSettings()

    DEFAULT_PHOENIX_SUFFIX: ClassVar[str] = "phoenix"
    PHOENIX_SUBNET_CIDR: ClassVar[str] = "10.0.36.0/24"

    # Docker Image settings
    repo_image_url: str = Field(
        default="ghcr.io/bbvch-ai/aihub-core/phoenix", description="URL of the Docker repository"
    )
    docker_image_tag: str = Field(description="Tag of the Docker image")

    # Azure settings
    app_service_plan_name: str = Field(description="Name of the Azure App Service Plan")

    # Registry settings
    registry_user: str = Field(
        default_factory=lambda: PhoenixConfig._registry_settings.REGISTRY_USER,
        description="Registry username for authentication",
    )
    registry_pat: str = Field(
        default_factory=lambda: PhoenixConfig._registry_settings.REGISTRY_PAT,
        description="Registry personal access token for authentication",
    )
    registry_url: str = Field(
        default_factory=lambda: PhoenixConfig._registry_settings.REGISTRY_URL,
        description="Registry URL for authentication",
    )

    # OAuth2 settings
    client_id: str = Field(description="Client ID for OAuth2 authentication")
    client_secret: str = Field(description="Client secret for OAuth2 authentication")
    oidc_config_url: str = Field(description="OIDC configuration URL for OAuth2 authentication")

    phoenix_secret: str = Field(description="Secret for Phoenix authentication")

    version: str = Field(description="Version of the Phoenix service")

    postgres_username: str = Field(
        default_factory=lambda: PhoenixConfig._postgres_settings.POSTGRES_USERNAME,
        description="Username for the PostgreSQL database",
    )
    postgres_password: str = Field(
        default_factory=lambda: PhoenixConfig._postgres_settings.POSTGRES_PASSWORD,
        description="Password for the PostgreSQL database",
    )

    database_name: str = "phoenix"

    @property
    def service_name(self) -> str:
        return self.resource_namer.app_service_name(PhoenixConfig.DEFAULT_PHOENIX_SUFFIX)

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"DOCKER|{self.repo_image_url}:{self.docker_image_tag}"

    @property
    def postgres_name(self) -> str:
        return self.resource_namer.postgres_name()
