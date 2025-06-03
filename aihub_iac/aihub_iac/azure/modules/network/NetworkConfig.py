from typing import ClassVar

from aihub_iac.azure.resources.BaseConfig import BaseConfig


class NetworkConfig(BaseConfig):
    """Configuration class for Nats infrastructure"""

    VNET_ADDRESS_SPACE: ClassVar[str] = "10.0.0.0/16"
    APP_SUBNET_CIDR: ClassVar[str] = "10.0.2.0/23"
    AGENTS_SUBNET_CIDR: ClassVar[str] = "10.0.16.0/20"
