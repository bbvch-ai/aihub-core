from pydantic import BaseModel
import os

from aihub_iac.azure.constants.resources import CONTAINER_APP, STORAGE_ACCOUNT, POSTGRES
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.OAuthSettings import OAuthSettings
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings


class DagsterConfig(StorageConfig):
    """Configuration class for Dagster infrastructure"""

    # Project and environment settings
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    # Docker Image settings
    repo_image_url: str
    docker_image_tag: str

    # Registry settings
    registry_user: str
    registry_pat: str
    registry_url: str = "ghcr.io"

    version: str

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
    oauth2_proxy_allowed_groups: str
    oauth2_proxy_oidc_groups_claim: str
    oauth2_proxy_redirect_url: str = None

    # Database settings
    postgres_username: str
    postgres_password: str

    # scaling
    webserver_min_replicas: int = 0
    webserver_max_replicas: int = 2

    # resources
    proxy_cpu: float = 0.5
    proxy_memory: str = "1Gi"
    webserver_cpu: float = 0.5
    webserver_memory: str = "1Gi"
    daemon_cpu: float = 2
    daemon_memory: str = "4Gi"

    database_name: str = "dagster"

    additional_env_vars: dict = {}

    @classmethod
    def from_env(
        cls,
        repo_image_url: str,
        docker_image_tag: str,
        oauth2_proxy_provider: str,
        oauth2_proxy_oidc_issuer_url: str,
        oauth2_proxy_email_domains: str,
        oauth2_proxy_custom_sign_in_logo: str,
        oauth2_proxy_reverse_proxy: str,
        oauth2_proxy_redirect_url: str,
        oauth2_proxy_allowed_groups: str,
        oauth2_proxy_oidc_groups_claim: str,
        oauth2_proxy_cookie_secret: str,
        oauth2_proxy_client_secret: str,
        version: str,
        additional_env_vars: dict = None,
    ) -> "DagsterConfig":
        """Create a configuration from environment variables"""
        # Load specific settings
        project_settings = ProjectSettings()
        registry_settings = RegistrySettings()
        postgres_settings = PostgresAuthSettings()
        auth_settings = OAuthSettings()
        return cls(
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            version=version,
            # Docker settings
            repo_image_url=repo_image_url,
            docker_image_tag=docker_image_tag,
            # Registry settings
            registry_user=registry_settings.REGISTRY_USER,
            registry_pat=registry_settings.REGISTRY_PAT,
            # OAuth2 settings
            oauth2_proxy_client_id=auth_settings.CLIENT_ID,
            oauth2_proxy_allowed_groups=oauth2_proxy_allowed_groups,
            oauth2_proxy_oidc_groups_claim=oauth2_proxy_oidc_groups_claim,
            oauth2_proxy_azure_tenant=auth_settings.TENANT_ID,
            oauth2_proxy_provider=oauth2_proxy_provider,
            oauth2_proxy_oidc_issuer_url=oauth2_proxy_oidc_issuer_url,
            oauth2_proxy_cookie_secret=oauth2_proxy_cookie_secret,
            oauth2_proxy_client_secret=oauth2_proxy_client_secret,
            oauth2_proxy_email_domains=oauth2_proxy_email_domains,
            oauth2_proxy_custom_sign_in_logo=oauth2_proxy_custom_sign_in_logo,
            oauth2_proxy_reverse_proxy=oauth2_proxy_reverse_proxy,
            oauth2_proxy_redirect_url=oauth2_proxy_redirect_url,
            # Database settings
            postgres_username=postgres_settings.POSTGRES_USERNAME,
            postgres_password=postgres_settings.POSTGRES_PASSWORD,
            additional_env_vars=additional_env_vars or {},
        )

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"{self.repo_image_url}:{self.docker_image_tag}"

    @property
    def dagster_webserver(self) -> str:
        """Generate the full docker image string"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}-{CONTAINER_APP}-{project_settings.LOCATION_SHORT}-dagster"

    @property
    def dagster_daemon(self) -> str:
        """Generate the full docker image string"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}-{CONTAINER_APP}-{project_settings.LOCATION_SHORT}-dagster-daemon"

    @property
    def dagster_datalake(self) -> str:
        """Generate the full docker image string"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}{STORAGE_ACCOUNT}{project_settings.LOCATION_SHORT}datalake"

    @property
    def storage_service_name(self) -> str:
        """Service name to use for storage resources"""
        return "datalake"

    @property
    def postgres_name(self) -> str:
        return f"{self.project_name}-{POSTGRES}-{self.location_short}"
