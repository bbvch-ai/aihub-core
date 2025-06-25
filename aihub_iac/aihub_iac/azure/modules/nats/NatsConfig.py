from typing import ClassVar

from pydantic import Field

from aihub_iac.azure.constants.suffix import DEFAULT_NATS_SUFFIX, DEFAULT_REDIS_SUFFIX
from aihub_iac.azure.resources.BaseConfig import BaseConfig
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class NatsConfig(StorageConfig, BaseConfig):
    """Configuration class for Nats infrastructure"""

    _registry_settings: ClassVar[RegistrySettings] = RegistrySettings()

    NATS_SUBNET_CIDR: ClassVar[str] = "10.0.1.0/29"
    NATS_STORAGE_SUBNET_CIDR: ClassVar[str] = "10.0.32.0/24"

    # Required fields
    nats_image_tag: str = Field(description="NATS image tag")
    redis_image_tag: str = Field(description="Redis image tag")

    # Registry settings
    registry_user: str = Field(
        default_factory=lambda: NatsConfig._registry_settings.REGISTRY_USER,
        description="Registry username for authentication",
    )
    registry_pat: str = Field(
        default_factory=lambda: NatsConfig._registry_settings.REGISTRY_PAT,
        description="Registry personal access token for authentication",
    )

    nats_cpu: int = Field(default=2, description="NATS CPU cores")
    nats_memory: int = Field(default=4, description="NATS memory in GB")
    redis_cpu: int = Field(default=2, description="Redis CPU cores")
    redis_memory: int = Field(default=4, description="Redis memory in GB")

    # Fields with default values
    nats_volume: str = Field(default="azurefilevolume", description="NATS volume name")
    redis_volume: str = Field(default="azurefilevolumeredis", description="Redis volume name")

    @property
    def nats_service_name(self) -> str:
        return self.resource_namer.app_service_name(DEFAULT_NATS_SUFFIX)

    @property
    def redis_service_name(self) -> str:
        return self.resource_namer.app_service_name(DEFAULT_REDIS_SUFFIX)

    @property
    def container_instance_name(self) -> str:
        return self.resource_namer.container_instance_name(DEFAULT_NATS_SUFFIX)

    @property
    def storage_service_name(self) -> str:
        """Service name to use for storage resources"""
        return "nats"
