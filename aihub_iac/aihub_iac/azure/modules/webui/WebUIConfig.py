from typing import ClassVar, Optional

from pydantic import Field, validator, computed_field

from aihub_iac.azure.constants.suffix import DEFAULT_API_SUFFIX, DEFAULT_WEBUI_SUFFIX
from aihub_iac.azure.modules.webui.OpenWebUIConfig import OpenWebUIConfig
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class WebUIConfig(StorageConfig):
    """Configuration class for WebUI infrastructure"""

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

    # Resources
    cpu: float = Field(default=2, description="CPU cores for the container")
    memory: str = Field(default="4Gi", description="Memory for the container")
    min_replicas: int = Field(default=1, description="Minimum number of replicas for the container")
    max_replicas: Optional[int] = Field(default=None, description="Maximum number of replicas for the container")

    # Registry settings - Direct authentication
    registry_user: str = Field(
        default_factory=lambda: WebUIConfig._registry_settings.REGISTRY_USER,
        description="Registry username for authentication",
    )
    registry_pat: Optional[str] = Field(
        default_factory=lambda: WebUIConfig._registry_settings.REGISTRY_PAT,
        description="Registry personal access token for authentication (optional if using Key Vault)",
    )
    registry_url: str = Field(
        default_factory=lambda: WebUIConfig._registry_settings.REGISTRY_URL or "https://ghcr.io",
        description="Registry URL for authentication",
    )

    # Key Vault settings - Alternative authentication
    key_vault_name: Optional[str] = Field(
        default=None,
        description="Azure Key Vault name for retrieving GitHub App token (optional, alternative to registry_pat)"
    )


    def uses_keyvault_auth(self) -> bool:
        """Check if Key Vault authentication is configured and should be used"""
        return (
                self.key_vault_name is not None and
                self.key_vault_name.strip() != ""
        )

    def registry_auth_method(self) -> str:
        """Get a string describing the authentication method being used"""
        return "keyvault" if self.uses_keyvault_auth() else "direct"

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

    def get_registry_secret_name(self) -> str:
        """Get the secret name to use for registry authentication"""
        return "github-app-token" if self.uses_keyvault_auth() else "registry-password"

    def requires_managed_identity(self) -> bool:
        """Check if managed identity is required for this configuration"""
        return self.uses_keyvault_auth()

    def get_keyvault_secret_url(self) -> Optional[str]:
        """Get the Key Vault secret URL for GitHub App token"""
        if not self.uses_keyvault_auth():
            return None
        return f"https://{self.key_vault_name}.vault.azure.net/secrets/github-app-access-token"