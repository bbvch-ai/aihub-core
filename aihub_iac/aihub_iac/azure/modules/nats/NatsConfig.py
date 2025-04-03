from dataclasses import dataclass
from typing import Optional

from aihub_iac.azure.constants.resources import APP_SERVICE, CONTAINER_INSTANCE
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


@dataclass
class NatsConfig(StorageConfig):
    """Configuration class for Nats infrastructure"""

    stack: str
    name: str
    subscription_id: str
    nats_image_tag: str
    redis_image_tag: str
    nats_volume: str = "azurefilevolume"
    redis_volume: str = "azurefilevolumeredis"
    registry_user: Optional[str] = None
    registry_pat: Optional[str] = None

    @classmethod
    def from_env(cls, stack: str, name: str, nats_image_tag: str, redis_image_tag: str) -> "NatsConfig":
        """Create a configuration from environment variables"""
        return cls(
            stack=stack,
            name=name,
            nats_image_tag=nats_image_tag,
            redis_image_tag=redis_image_tag,
            project_name=ProjectSettings().APP_NAME,
            location=ProjectSettings().LOCATION,
            location_short=ProjectSettings().LOCATION_SHORT,
            resource_group=ProjectSettings().RESOURCE_GROUP,
            subscription_id=ProjectSettings().ARM_SUBSCRIPTION_ID,
            registry_user=RegistrySettings().REGISTRY_USER,
            registry_pat=RegistrySettings().REGISTRY_PAT,
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
