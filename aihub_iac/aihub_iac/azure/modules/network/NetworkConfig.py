from pydantic import BaseModel, Field, computed_field

from aihub_iac.azure.constants.resources import APP_SERVICE, CONTAINER_INSTANCE, V_NET, LOG_WORKSPACE
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.resources.BaseConfig import BaseConfig
from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings
from aihub_iac.azure.settings.RegistrySettings import RegistrySettings


class NetworkConfig(BaseConfig):
    """Configuration class for Nats infrastructure"""

    pass
