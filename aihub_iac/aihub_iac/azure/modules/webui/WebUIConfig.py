from pydantic import BaseModel, computed_field

from aihub_iac.azure.constants.resources import (
    LOG_WORKSPACE,
    CONTAINER_APP_ENVIRONMENT,
    STORAGE_ACCOUNT,
    APP_SERVICE,
    CONTAINER_APP,
    POSTGRES,
)
from aihub_iac.azure.modules.webui.OpenWebUIConfig import OpenWebUIConfig
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class WebUIConfig(StorageConfig):
    """Configuration class for Nats infrastructure"""

    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    openwebui_config: OpenWebUIConfig

    volume_name: str = "webuivolume"
    db_name: str = "webui"
    pg_vector_db_name: str = "pgvector"

    postgres_username: str
    postgres_password: str

    # Docker Image settings
    repo_image_url: str
    docker_image_tag: str

    # resources
    cpu: float = 2
    memory: str = "4Gi"

    # Registry settings
    registry_user: str
    registry_pat: str
    registry_url: str = "ghcr.io"

    @classmethod
    def from_env(
        cls,
        repo_image_url: str,
        docker_image_tag: str,
        openwebui_config: OpenWebUIConfig,
    ) -> "WebUIConfig":
        """Create a configuration from environment variables"""
        project_settings = ProjectSettings()
        postgres_auth_settings = PostgresAuthSettings()
        registry_settings = RegistrySettings()

        return cls(
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            openwebui_config=openwebui_config,
            postgres_username=postgres_auth_settings.POSTGRES_USERNAME,
            postgres_password=postgres_auth_settings.POSTGRES_PASSWORD,
            # Registry settings
            registry_user=registry_settings.REGISTRY_USER,
            registry_pat=registry_settings.REGISTRY_PAT,
            # Docker settings
            repo_image_url=repo_image_url,
            docker_image_tag=docker_image_tag,
        )

    @property
    def log_analytics_name(self) -> str:
        return f"{self.project_name}-{LOG_WORKSPACE}-{self.location_short}-webui"

    @property
    def webui_container_env(self) -> str:
        return f"{self.project_name}-{CONTAINER_APP_ENVIRONMENT}-{self.location_short}-webui"

    @property
    def webui_container_app(self) -> str:
        return f"{self.project_name}-{CONTAINER_APP}-{self.location_short}-webui"

    @property
    def webui_storage(self) -> str:
        return f"{self.project_name}{STORAGE_ACCOUNT}{self.location_short}webui"

    @property
    def api_service_name(self) -> str:
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short}-api"

    @property
    def postgres_name(self) -> str:
        return f"{self.project_name}-{POSTGRES}-{self.location_short}"

    @property
    def storage_service_name(self) -> str:
        """Service name to use for storage resources"""
        return "webui"

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"{self.repo_image_url}:{self.docker_image_tag}"
