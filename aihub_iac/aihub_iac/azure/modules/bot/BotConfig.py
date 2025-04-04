from pydantic import BaseModel, Field, computed_field

from aihub_iac.azure.constants.resources import APP_SERVICE, COSMOS
from aihub_iac.azure.settings.OAuthSettings import OAuthSettings
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class BotConfig(BaseModel):
    """Configuration class for Bot service infrastructure"""

    # Basic configuration
    stack: str
    name: str

    # Project and environment settings
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str

    # Docker Image settings
    repo_image_url: str
    docker_image_tag: str

    # Azure settings
    app_service_plan_name: str
    cosmos_account_name: str
    cosmos_resource_group: str

    # Anonymization settings
    anonym_name: str
    anonym_email: str
    anonym_roles: str
    anonym_oid: str

    # Registry settings
    registry_user: str
    registry_pat: str
    registry_url: str

    # OAuth2 settings
    client_id: str
    tenant_id: str
    authority_url: str

    nats_endpoint: str
    version: str

    @classmethod
    def from_env(
        cls,
        stack: str,
        name: str,
        repo_image_url: str,
        docker_image_tag: str,
        app_service_plan_name: str,
        cosmos_account_name: str,
        cosmos_resource_group: str,
        anonym_name: str,
        anonym_email: str,
        anonym_roles: str,
        anonym_oid: str,
        nats_endpoint: str,
        version: str,
    ) -> "BotConfig":
        """Create a configuration from environment variables and BotConfig"""
        project_settings = ProjectSettings()
        registry_settings = RegistrySettings()
        oauth_settings = OAuthSettings()

        return cls(
            stack=stack,
            name=name,
            repo_image_url=repo_image_url,
            docker_image_tag=docker_image_tag,
            app_service_plan_name=app_service_plan_name,
            cosmos_account_name=cosmos_account_name,
            cosmos_resource_group=cosmos_resource_group,
            anonym_name=anonym_name,
            anonym_email=anonym_email,
            anonym_roles=anonym_roles,
            anonym_oid=anonym_oid,
            nats_endpoint=nats_endpoint,
            version=version,
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            registry_user=registry_settings.REGISTRY_USER,
            registry_pat=registry_settings.REGISTRY_PAT,
            registry_url=registry_settings.REGISTRY_URL,
            client_id=oauth_settings.CLIENT_ID,
            tenant_id=oauth_settings.TENANT_ID,
            authority_url=oauth_settings.AUTHORITY_URL,
        )

    @computed_field
    def service_name(self) -> str:
        """Generate the service name"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}-{APP_SERVICE}-{project_settings.LOCATION_SHORT}-bot"

    @computed_field
    def cosmos_name(self) -> str:
        """Generate the cosmos name"""
        project_settings = ProjectSettings()
        return f"{project_settings.APP_NAME}-{COSMOS}-{project_settings.LOCATION_SHORT}-api"

    @computed_field
    def effective_cosmos_account_name(self) -> str:
        """Get the effective cosmos account name, using the configured value or generating one"""
        return self.cosmos_account_name or self.cosmos_name

    @computed_field
    def effective_cosmos_resource_group(self) -> str:
        """Get the effective cosmos resource group, using the configured value or the default"""
        return self.cosmos_resource_group or ProjectSettings().RESOURCE_GROUP

    @computed_field
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"DOCKER|{self.repo_image_url}:{self.docker_image_tag}"
