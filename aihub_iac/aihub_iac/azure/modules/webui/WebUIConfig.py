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


class WebUIConfig(StorageConfig):
    """Configuration class for Nats infrastructure"""

    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    openwebui_config: OpenWebUIConfig

    volume_name = "webuivolume"
    db_name = "webui"
    pg_vector_db_name = "pgvector"

    postgres_username: str
    postgres_password: str

    redis_endpoint: str

    @classmethod
    def from_env(
        cls,
        openwebui_config: OpenWebUIConfig,
        redis_endpoint: str,
    ) -> "WebUIConfig":
        """Create a configuration from environment variables"""
        project_settings = ProjectSettings()
        postgres_auth_settings = PostgresAuthSettings()

        return cls(
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            openwebui_config=openwebui_config,
            postgres_username=postgres_auth_settings.POSTGRES_USERNAME,
            postgres_password=postgres_auth_settings.POSTGRES_PASSWORD,
            redis_endpoint=redis_endpoint,
        )

    @computed_field
    def log_analytics_name(self) -> str:
        return f"{self.project_name}-{LOG_WORKSPACE}-{self.location_short}-webui"

    @computed_field
    def webui_container_env(self) -> str:
        return f"{self.project_name}-{CONTAINER_APP_ENVIRONMENT}-{self.location_short}-webui"

    @computed_field
    def webui_container_app(self) -> str:
        return f"{self.project_name}-{CONTAINER_APP}-{self.location_short}-webui"

    @computed_field
    def webui_storage(self) -> str:
        return f"{self.project_name}{STORAGE_ACCOUNT}{self.location_short_name}webui"

    @computed_field
    def api_service_name(self) -> str:
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-api"

    @computed_field
    def postgres_name(self) -> str:
        return f"{self.project_name}-{POSTGRES}-{self.location_short}"

    @computed_field
    def storage_service_name(self) -> str:
        """Service name to use for storage resources"""
        return "webui"
