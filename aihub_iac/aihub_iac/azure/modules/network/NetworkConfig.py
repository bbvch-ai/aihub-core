from pydantic import BaseModel, Field, computed_field

from aihub_iac.azure.constants.resources import APP_SERVICE, CONTAINER_INSTANCE, V_NET
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class NetworkConfig(BaseModel):
    """Configuration class for Nats infrastructure"""

    # Required fields
    project_name: str
    location: str
    location_short: str
    resource_group: str
    subscription_id: str
    network_provider: NetworkProvider

    @classmethod
    def from_env(cls) -> "NetworkConfig":
        """Create a configuration from environment variables"""
        project_settings = ProjectSettings()
        return cls(
            project_name=project_settings.APP_NAME,
            location=project_settings.LOCATION,
            location_short=project_settings.LOCATION_SHORT,
            resource_group=project_settings.RESOURCE_GROUP,
            subscription_id=project_settings.ARM_SUBSCRIPTION_ID,
            network_provider=NetworkProvider(
                project_settings.RESOURCE_GROUP, project_settings.APP_NAME, project_settings.LOCATION_SHORT
            ),
        )

    @computed_field
    def v_net_name(self) -> str:
        return self.network_provider.v_net_name

    @computed_field
    def nats_subnet_name(self) -> str:
        return self.network_provider.nats_subnet_name

    @computed_field
    def app_subnet_name(self) -> str:
        return self.network_provider.app_subnet_name

    @computed_field
    def pg_subnet_name(self) -> str:
        return self.network_provider.pg_subnet_name

    @computed_field
    def cap_subnet_name(self) -> str:
        return self.network_provider.cap_subnet_name

    @computed_field
    def agents_subnet_name(self) -> str:
        return self.network_provider.agents_subnet_name

    @computed_field
    def priv_endpoint_subnet_name(self) -> str:
        return self.network_provider.priv_endpoint_subnet_name
