from typing import Annotated, ClassVar

from pydantic import Field

from aihub_iac.azure.constants.suffix import DEFAULT_DAEMON_SUFFIX, DEFAULT_WEBSERVER_SUFFIX
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.OAuthSettings import OAuthSettings
from aihub_iac.azure.settings.PostgresAuthSettings import PostgresAuthSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class DagsterConfig(StorageConfig):
    """Configuration class for Dagster infrastructure"""

    _registry_settings: ClassVar[RegistrySettings] = RegistrySettings()
    _oauth_settings: ClassVar[OAuthSettings] = OAuthSettings()
    _postgres_settings: ClassVar[PostgresAuthSettings] = PostgresAuthSettings()

    DAGSTER_SUBNET_CIDR: ClassVar[str] = "10.0.38.0/23"
    DAGSTER_STORAGE_SUBNET_CIDR: ClassVar[str] = "10.0.35.0/24"

    # Docker Image settings
    repo_image_url: Annotated[str, Field(description="URL of the Docker repository")]
    docker_image_tag: Annotated[str, Field(description="Tag of the Docker image")]

    # Registry settings
    registry_user: Annotated[
        str,
        Field(
            default_factory=lambda: DagsterConfig._registry_settings.REGISTRY_USER,
            description="Registry username for authentication",
        ),
    ]
    registry_pat: Annotated[
        str,
        Field(
            default_factory=lambda: DagsterConfig._registry_settings.REGISTRY_PAT,
            description="Registry personal access token for authentication",
        ),
    ]
    registry_url: Annotated[
        str,
        Field(
            default_factory=lambda: DagsterConfig._registry_settings.REGISTRY_URL,
            description="Registry URL for authentication",
        ),
    ]

    version: Annotated[str, Field(description="Version of the API service")]

    # OAuth2 settings
    oauth2_proxy_client_id: Annotated[
        str,
        Field(default_factory=lambda: DagsterConfig._oauth_settings.CLIENT_ID, description="Client ID of OAuth2 proxy"),
    ]
    oauth2_proxy_azure_tenant: Annotated[
        str,
        Field(
            default_factory=lambda: DagsterConfig._oauth_settings.TENANT_ID,
            description="Azure tenant ID for OAuth2 proxy",
        ),
    ]
    oauth2_proxy_provider: Annotated[str, Field(description="OAuth2 provider for authentication")]
    oauth2_proxy_oidc_issuer_url: Annotated[str, Field(description="OIDC issuer URL for OAuth2 proxy")]
    oauth2_proxy_cookie_secret: Annotated[str, Field(description="Cookie secret for OAuth2 proxy")]
    oauth2_proxy_client_secret: Annotated[str, Field(description="Client secret for OAuth2 proxy")]
    oauth2_proxy_email_domains: Annotated[str, Field(description="Email domains for OAuth2 proxy")]
    oauth2_proxy_custom_sign_in_logo: Annotated[str, Field(description="Custom sign-in logo for OAuth2 proxy")]
    oauth2_proxy_reverse_proxy: Annotated[str, Field(description="Reverse proxy setting for OAuth2 proxy")]
    oauth2_proxy_allowed_groups: Annotated[str, Field(description="Allowed groups for OAuth2 proxy")]
    oauth2_proxy_oidc_groups_claim: Annotated[str, Field(description="OIDC groups claim for OAuth2 proxy")]
    oauth2_proxy_redirect_url: Annotated[str, Field(description="Redirect URL for OAuth2 proxy")]

    # Database settings
    postgres_username: Annotated[
        str,
        Field(
            default_factory=lambda: DagsterConfig._postgres_settings.POSTGRES_USERNAME,
            description="Username for the PostgreSQL database",
        ),
    ]
    postgres_password: Annotated[
        str,
        Field(
            default_factory=lambda: DagsterConfig._postgres_settings.POSTGRES_PASSWORD,
            description="Password for the PostgreSQL database",
        ),
    ]

    # scaling
    webserver_min_replicas: Annotated[int, Field(description="Minimum number of replicas for the webserver")] = 0
    webserver_max_replicas: Annotated[int, Field(description="Maximum number of replicas for the webserver")] = 2

    # resources
    proxy_cpu: Annotated[float, Field(description="CPU allocation in cores for the proxy container")] = 0.5
    proxy_memory: Annotated[str, Field(description="Memory allocation in GB for the proxy container")] = "1Gi"
    webserver_cpu: Annotated[float, Field(description="CPU allocation in cores for the webserver container")] = 1.5
    webserver_memory: Annotated[str, Field(description="Memory allocation in GB for the webserver container")] = "3Gi"
    daemon_cpu: Annotated[float, Field(description="CPU allocation in cores for the daemon container")] = 2
    daemon_memory: Annotated[str, Field(description="Memory allocation in GB for the daemon container")] = "4Gi"

    database_name: str = "dagster"

    additional_env_vars: dict = {}

    @property
    def effective_docker_image(self) -> str:
        return f"{self.repo_image_url}:{self.docker_image_tag}"

    @property
    def dagster_webserver(self) -> str:
        return self.resource_namer.container_app_name(DEFAULT_WEBSERVER_SUFFIX)

    @property
    def dagster_daemon(self) -> str:
        return self.resource_namer.container_app_name(DEFAULT_DAEMON_SUFFIX)

    @property
    def storage_service_name(self) -> str:
        return "datalake"

    @property
    def postgres_name(self) -> str:
        return self.resource_namer.postgres_name()
