from pydantic import BaseModel
import os

from aihub_iac.azure.constants.resources import CONTAINER_APP, STORAGE_ACCOUNT
from aihub_iac.azure.settings.OAuthSettings import OAuthSettings
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings


class DagsterConfig(BaseModel):
    """Configuration class for Dagster infrastructure"""

    # Project and environment settings
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    app_name: str
    azure_subscription_name: str
    version: str

    # Docker Image settings
    repo_image_url: str
    docker_image_tag: str
    docker_compose_path: str = "./../../../../pipelines/docker-compose.yml"

    # Azure settings
    app_service_plan_name: str

    # Registry settings
    registry_user: str
    registry_pat: str
    registry_url: str = "https://ghcr.io"

    # OAuth2 settings
    oauth2_proxy_client_id: str
    oauth2_proxy_azure_tenant: str
    oauth2_proxy_provider: str
    oauth2_proxy_oidc_issuer_url: str
    oauth2_proxy_cookie_secret: str
    oauth2_proxy_client_secret: str
    oauth2_proxy_email_domains: str
    oauth2_proxy_custom_sign_in_logo: str
    oauth2_proxy_reverse_proxy: str
    oauth2_proxy_redirect_url: str = None

    # Database settings
    postgres_username: str
    postgres_password: str
    database_name: str = "dagster"

    @classmethod
    def from_env(
        cls,
        oauth2_proxy_provider: str,
        oauth2_proxy_oidc_issuer_url: str,
        oauth2_proxy_email_domains: str,
        oauth2_proxy_custom_sign_in_logo: str,
        oauth2_proxy_reverse_proxy: str,
        oauth2_proxy_redirect_url: str,
    ) -> "DagsterConfig":
        """Create a configuration from environment variables"""
        # Load specific settings
        project_settings = ProjectSettings()
        registry_settings = RegistrySettings()
        postgres_settings = PostgresAuthSettings()
        auth_settings = OAuthSettings()
        auth_settings.
        return cls(
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            azure_subscription_name=os.getenv("AZURE_SUBSCRIPTION_NAME"),
            version=os.getenv("VERSION"),
            # Docker settings
            repo_image_url=os.getenv("DAGSTER_REPO_IMAGE_URL"),
            docker_image_tag=os.getenv("DAGSTER_IMAGE_TAG"),
            # Registry settings
            registry_user=registry_settings.REGISTRY_USER,
            registry_pat=registry_settings.REGISTRY_PAT,
            registry_url=registry_settings.REGISTRY_URL,
            # OAuth2 settings
            oauth2_proxy_client_id=auth_settings.CLIENT_ID,
            oauth2_proxy_azure_tenant=auth_settings.TENANT_ID,
            oauth2_proxy_provider=oauth2_proxy_provider,
            oauth2_proxy_oidc_issuer_url=oauth2_proxy_oidc_issuer_url,
            oauth2_proxy_cookie_secret=os.getenv("OAUTH2_PROXY_COOKIE_SECRET"),
            oauth2_proxy_client_secret=os.getenv("OAUTH2_PROXY_CLIENT_SECRET"),
            oauth2_proxy_email_domains=oauth2_proxy_email_domains,
            oauth2_proxy_custom_sign_in_logo=oauth2_proxy_custom_sign_in_logo,
            oauth2_proxy_reverse_proxy=oauth2_proxy_reverse_proxy,
            oauth2_proxy_redirect_url=oauth2_proxy_redirect_url,
            # Database settings
            postgres_username=postgres_settings.POSTGRES_USERNAME,
            postgres_password=postgres_settings.POSTGRES_PASSWORD,
            # Create resource namer
        )

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"{self.repo_image_url}:{self.docker_image_tag}"

    @property
    def dagster_service(self) -> str:
        """Generate the full docker image string"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}-{CONTAINER_APP}-{project_settings.LOCATION_SHORT}-dagster"

    @property
    def dagster_datalake(self) -> str:
        """Generate the full docker image string"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}{STORAGE_ACCOUNT}{project_settings.LOCATION_SHORT}datalake"
