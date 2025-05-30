from typing import ClassVar

from pydantic import Field

from aihub_iac.azure.constants.suffix import DEFAULT_API_SUFFIX, DEFAULT_WEBUI_SUFFIX
from aihub_iac.azure.modules.api.ApiConfig import ApiConfig
from aihub_iac.azure.modules.webui.OpenWebUIConfig import OpenWebUIConfig
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class WebUIConfig(StorageConfig):
    """Configuration class for Nats infrastructure"""

    _postgres_settings: ClassVar[PostgresAuthSettings] = PostgresAuthSettings()
    _registry_settings: ClassVar[RegistrySettings] = RegistrySettings()

    WEBUI_SUBNET_CIDR: ClassVar[str] = "10.0.40.0/23"
    WEBUI_STORAGE_SUBNET_CIDR: ClassVar[str] = "10.0.42.0/24"

    openwebui_config: OpenWebUIConfig

    volume_name: str = Field(default="webuivolume", description="Volume name for the container")
    db_name: str = Field(default="webui", description="Database name for the PostgreSQL database")
    pg_vector_db_name: str = Field(default="pgvector", description="Database name for the pgvector database")

    postgres_username: str = Field(
        default_factory=lambda: WebUIConfig._postgres_settings.POSTGRES_USERNAME,
        description="Username for the PostgreSQL database",
    )
    postgres_password: str = Field(
        default_factory=lambda: WebUIConfig._postgres_settings.POSTGRES_PASSWORD,
        description="Password for the PostgreSQL database",
    )

    # Docker Image settings
    repo_image_url: str = Field(description="URL of the Docker repository")
    docker_image_tag: str = Field(description="Tag of the Docker image")

    # resources
    cpu: float = Field(default=2, description="CPU cores for the container")
    memory: str = Field(default="4Gi", description="Memory for the container")

    # Registry settings
    registry_user: str = Field(
        default_factory=lambda: WebUIConfig._registry_settings.REGISTRY_USER,
        description="Registry username for authentication",
    )
    registry_pat: str = Field(
        default_factory=lambda: WebUIConfig._registry_settings.REGISTRY_PAT,
        description="Registry personal access token for authentication",
    )
    registry_url: str = Field(
        default_factory=lambda: WebUIConfig._registry_settings.REGISTRY_URL or "https://ghcr.io",
        description="Registry URL for authentication",
    )

    @property
    def log_analytics_name(self) -> str:
        return self.resource_namer.log_workspace(DEFAULT_WEBUI_SUFFIX)

    @property
    def webui_container_env(self) -> str:
        return self.resource_namer.container_app_environment_name(DEFAULT_WEBUI_SUFFIX)

    @property
    def webui_container_app(self) -> str:
        return self.resource_namer.container_app_name(DEFAULT_WEBUI_SUFFIX)

    @property
    def webui_storage(self) -> str:
        return self.resource_namer.storage_account_name(DEFAULT_WEBUI_SUFFIX)

    @property
    def api_service_name(self) -> str:
        return self.resource_namer.app_service_name(DEFAULT_API_SUFFIX)

    @property
    def postgres_name(self) -> str:
        return self.resource_namer.postgres_name()

    @property
    def storage_service_name(self) -> str:
        """Service name to use for storage resources"""
        return "webui"

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"{self.repo_image_url}:{self.docker_image_tag}"
