from pydantic import BaseModel, Field, computed_field

from aihub_iac.azure.constants.resources import APP_SERVICE, CONTAINER_INSTANCE
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class NatsConfig(StorageConfig):
    """Configuration class for Nats infrastructure"""

    # Required fields
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str
    nats_image_tag: str
    redis_image_tag: str
    registry_user: str
    registry_pat: str
    nats_cpu: int = 2
    nats_memory: int = 4
    redis_cpu: int = 2
    redis_memory: int = 4

    # Fields with default values
    nats_volume: str = "azurefilevolume"
    redis_volume: str = "azurefilevolumeredis"

    @classmethod
    def from_env(cls, nats_image_tag: str, redis_image_tag: str, **kwargs) -> "NatsConfig":
        """Create a configuration from environment variables"""
        project_settings = ProjectSettings()
        registry_settings = RegistrySettings()

        return cls(
            nats_image_tag=nats_image_tag,
            redis_image_tag=redis_image_tag,
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            registry_user=registry_settings.REGISTRY_USER,
            registry_pat=registry_settings.REGISTRY_PAT,
            **kwargs,
        )

    @property
    def nats_service_name(self) -> str:
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short}-nats"

    @property
    def redis_service_name(self) -> str:
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short}-redis"

    @property
    def container_instance_name(self) -> str:
        return f"{self.project_name}-{CONTAINER_INSTANCE}-{self.location_short}-nats"

    @property
    def storage_service_name(self) -> str:
        """Service name to use for storage resources"""
        return "nats"
