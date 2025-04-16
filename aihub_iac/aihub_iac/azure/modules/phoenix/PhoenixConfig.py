from pydantic import BaseModel

from aihub_iac.azure.constants.resources import APP_SERVICE, POSTGRES
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class PhoenixConfig(BaseModel):
    """Configuration class for API service infrastructure"""

    # Project and environment settings
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    # Docker Image settings
    repo_image_url: str = "ghcr.io/bbvch-ai/aihub-core/phoenix"
    docker_image_tag: str

    # Azure settings
    app_service_plan_name: str

    # Registry settings
    registry_user: str
    registry_pat: str
    registry_url: str

    # OAuth2 settings
    client_id: str
    client_secret: str
    oidc_config_url: str

    phoenix_secret: str

    version: str

    postgres_password: str
    postgres_username: str

    database_name: str = "phoenix"

    @classmethod
    def from_env(
        cls,
        docker_image_tag: str,
        app_service_plan_name: str,
        phoenix_secret: str,
        version: str,
        client_id: str,
        client_secret: str,
        oidc_config_url: str,
    ) -> "PhoenixConfig":
        """Create a configuration from environment variables and ApiConfig"""
        project_settings = ProjectSettings()
        registry_settings = RegistrySettings()
        postgres_settings = PostgresAuthSettings()

        return cls(
            docker_image_tag=docker_image_tag,
            app_service_plan_name=app_service_plan_name,
            version=version,
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            registry_user=registry_settings.REGISTRY_USER,
            registry_pat=registry_settings.REGISTRY_PAT,
            registry_url=registry_settings.REGISTRY_URL,
            phoenix_secret=phoenix_secret,
            client_id=client_id,
            client_secret=client_secret,
            oidc_config_url=oidc_config_url,
            postgres_username=postgres_settings.POSTGRES_USERNAME,
            postgres_password=postgres_settings.POSTGRES_PASSWORD,
        )

    @property
    def service_name(self) -> str:
        """Generate the service name"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}-{APP_SERVICE}-{project_settings.LOCATION_SHORT}-phoenix"

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"DOCKER|{self.repo_image_url}:{self.docker_image_tag}"

    @property
    def postgres_name(self) -> str:
        return f"{self.project_name}-{POSTGRES}-{self.location_short}"
