from typing import ClassVar, Optional

from pydantic import Field

from aihub_iac.azure.modules.nats.NatsConfig import NatsConfig
from aihub_iac.azure.resources.BaseConfig import BaseConfig
from aihub_iac.azure.settings.OAuthSettings import OAuthSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class BotConfig(BaseConfig):
    """Configuration class for Bot service infrastructure"""

    _registry_settings: ClassVar[RegistrySettings] = RegistrySettings()
    _oauth_settings: ClassVar[OAuthSettings] = OAuthSettings()

    DEFAULT_BOT_SUFFIX: ClassVar[str] = "bot"

    # Docker Image settings
    repo_image_url: str = Field(description="URL of the Docker repository")
    docker_image_tag: str = Field(description="Tag of the Docker image")

    # Azure settings
    app_service_plan_name: str = Field(description="Name of the Azure App Service Plan")
    cosmos_account_name: Optional[str] = Field(description="Name of the Azure Cosmos DB account")
    cosmos_resource_group: Optional[str] = Field(description="Name of the Azure Cosmos DB resource group")

    # Anonymization settings
    anonym_name: str = Field(default="Aihub BOT", description="Anonymized name for the API service")
    anonym_email: str = Field(default="bot@ai-agents.ch", description="Anonymized email for the API service")
    anonym_roles: str = Field(default='["AllAgents"]', description="Anonymized roles for the API service")
    anonym_oid: str = Field(default="0123456789", description="Anonymized OID for the API service")

    # Registry settings
    registry_user: str = Field(
        default_factory=lambda: BotConfig._registry_settings.REGISTRY_USER,
        description="Registry username for authentication",
    )
    registry_pat: str = Field(
        default_factory=lambda: BotConfig._registry_settings.REGISTRY_PAT,
        description="Registry personal access token for authentication",
    )
    registry_url: str = Field(
        default_factory=lambda: BotConfig._registry_settings.REGISTRY_URL,
        description="Registry URL for authentication",
    )

    # OAuth2 settings
    client_id: str = Field(default_factory=lambda: BotConfig._oauth_settings.CLIENT_ID, description="Client ID")
    tenant_id: str = Field(default_factory=lambda: BotConfig._oauth_settings.TENANT_ID, description="Tenant ID")
    authority_url: str = Field(
        default_factory=lambda: BotConfig._oauth_settings.AUTHORITY_URL,
        description="Authority URL for OAuth2 authentication",
    )

    version: str = Field(description="Version of the Bot service")

    @property
    def service_name(self) -> str:
        return self.resource_namer.app_service_name(BotConfig.DEFAULT_BOT_SUFFIX)

    @property
    def effective_cosmos_account_name(self) -> str:
        return self.cosmos_account_name or self.resource_namer.cosmos_name()

    @property
    def effective_cosmos_resource_group(self) -> str:
        return self.cosmos_resource_group or self.resource_group

    @property
    def nats_container_group_name(self) -> str:
        return self.resource_namer.container_instance_name(NatsConfig.DEFAULT_NATS_SUFFIX)

    @property
    def effective_docker_image(self) -> str:
        return f"DOCKER|{self.repo_image_url}:{self.docker_image_tag}"
