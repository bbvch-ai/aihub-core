from dataclasses import dataclass

from aihub_iac.azure.constants.resources import APP_SERVICE, COSMOS
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings


@dataclass
class BotServiceConfig:
    """Configuration class for Bot service infrastructure"""

    stack: str
    name: str
    repo_image_url: str
    docker_image_tag: str
    cosmos_account_name: str
    cosmos_resource_group: str
    bot_anonym_name: str
    bot_anonym_email: str
    bot_anonym_roles: str
    bot_anonym_oid: str
    nats_endpoint: str
    version: str

    @classmethod
    def from_env(
        cls,
        stack: str,
        name: str,
        repo_image_url: str,
        docker_image_tag: str,
        cosmos_account_name: str,
        cosmos_resource_group: str,
        bot_anonym_name: str,
        bot_anonym_email: str,
        bot_anonym_roles: str,
        bot_anonym_oid: str,
        nats_endpoint: str,
        version: str,
    ) -> "BotServiceConfig":
        """Create a configuration from environment variables and BotConfig"""

        return cls(
            stack=stack,
            name=name,
            repo_image_url=repo_image_url,
            docker_image_tag=docker_image_tag,
            cosmos_account_name=cosmos_account_name,
            cosmos_resource_group=cosmos_resource_group,
            bot_anonym_name=bot_anonym_name,
            bot_anonym_email=bot_anonym_email,
            bot_anonym_roles=bot_anonym_roles,
            bot_anonym_oid=bot_anonym_oid,
            nats_endpoint=nats_endpoint,
            version=version,
        )

    @property
    def service_name(self) -> str:
        """Generate the service name"""
        return f"{ProjectSettings().APP_NAME}-{APP_SERVICE}-{ProjectSettings().LOCATION_SHORT}-bot"

    @property
    def cosmos_name(self) -> str:
        """Generate the cosmos name"""
        return f"{ProjectSettings().APP_NAME}-{COSMOS}-{ProjectSettings().LOCATION_SHORT}-api"

    @property
    def effective_cosmos_account_name(self) -> str:
        """Get the effective cosmos account name, using the configured value or generating one"""
        return self.cosmos_account_name or self.cosmos_name

    @property
    def effective_cosmos_resource_group(self) -> str:
        """Get the effective cosmos resource group, using the configured value or the default"""
        return self.cosmos_resource_group or ProjectSettings().RESOURCE_GROUP

    @property
    def effective_docker_image(self) -> str:
        """Generate the full docker image string"""
        return f"DOCKER|{self.repo_image_url}:{self.docker_image_tag}"
