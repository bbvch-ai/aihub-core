import pulumi
from typing import Dict, Optional

from pulumi_azure_native import network, app, operationalinsights

from aihub_iac.azure.constants.resources import V_NET
from aihub_iac.azure.modules.network.NetworkConfig import NetworkConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider


class Network(pulumi.ComponentResource):
    """A Pulumi component resource for creating network infrastructure"""

    def __init__(self, stack: str, name: str, config: NetworkConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

        # Create configuration from environment or use provided config
        self.config = config
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location_short
        )

        # Store created resources
        self.v_net_name = f"{self.config.project_name}-{V_NET}-{self.config.location_short}"

        self.vnet = None
        self.subnets = {}

        # Create resources
        self._create_resources()

    def _create_resources(self):
        """Create all network resources"""
        # Create virtual network
        self.vnet = self._create_virtual_network()

        # Create subnets
        self.subnets["nats"] = self._create_nats_subnet()
        self.subnets["app"] = self._create_app_subnet()
        self.subnets["pg"] = self._create_pg_subnet()
        self.subnets["private_endpoint"] = self._create_private_endpoint_subnet()
        self.subnets["capp"] = self._create_capp_subnet()
        self.subnets["agents"] = self._create_agents_subnet()
        self.subnets["nats_storage"] = self._create_nats_storage_subnet()
        self.subnets["cosmos"] = self._create_cosmos_subnet()
        self.subnets["search"] = self._create_search_subnet()
        self.subnets["dagster_storage"] = self._create_dagster_storage_subnet()

        # Export outputs
        self._register_outputs()

    def _create_virtual_network(self) -> network.VirtualNetwork:
        """Create the virtual network"""
        return network.VirtualNetwork(
            virtual_network_name=self.network_provider.v_net_name,
            resource_name=self.network_provider.v_net_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            address_space=network.AddressSpaceArgs(address_prefixes=["10.0.0.0/16"]),  # 10.0.0.0 - 10.0.255.255
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_nats_subnet(self) -> network.Subnet:
        """Create the NATS subnet"""
        return network.Subnet(
            name=self.network_provider.nats_subnet_name,
            resource_name=self.network_provider.nats_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.1.0/29",  # 10.0.1.0 - 10.0.1.7
            delegations=[
                network.DelegationArgs(
                    name="aci-delegation",
                    service_name="Microsoft.ContainerInstance/containerGroups",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_app_subnet(self) -> network.Subnet:
        """Create the APP subnet for API, Bot, Dagster, Phoenix"""
        return network.Subnet(
            name=self.network_provider.app_subnet_name,
            resource_name=self.network_provider.app_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.2.0/23",  # 10.0.2.0 - 10.0.3.255
            delegations=[
                network.DelegationArgs(
                    name="app-delegation",
                    service_name="Microsoft.Web/serverFarms",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_pg_subnet(self) -> network.Subnet:
        """Create the Postgres subnet"""
        return network.Subnet(
            name=self.network_provider.pg_subnet_name,
            resource_name=self.network_provider.pg_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.4.0/24",  # 10.0.4.0 - 10.0.4.255
            delegations=[
                network.DelegationArgs(
                    name="postgres-delegation",
                    service_name="Microsoft.DBforPostgreSQL/flexibleServers",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_private_endpoint_subnet(self) -> network.Subnet:
        """Create the Private Endpoints subnet"""
        return network.Subnet(
            name=self.network_provider.priv_endpoint_subnet_name,
            resource_name=self.network_provider.priv_endpoint_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.6.0/24",  # 10.0.6.0 - 10.0.6.255
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_capp_subnet(self) -> network.Subnet:
        """Create the Container Apps subnet"""
        return network.Subnet(
            name=self.network_provider.cap_subnet_name,
            resource_name=self.network_provider.cap_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.8.0/23",  # 10.0.8.0 - 10.0.10.255
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_agents_subnet(self) -> network.Subnet:
        """Create the Agents subnet"""
        return network.Subnet(
            name=self.network_provider.agents_subnet_name,
            resource_name=self.network_provider.agents_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.16.0/20",  # 10.0.16.0 - 10.0.31.255
            delegations=[
                network.DelegationArgs(
                    name="aci-agent-delegation",
                    service_name="Microsoft.ContainerInstance/containerGroups",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_nats_storage_subnet(self) -> network.Subnet:
        """Create the Agents subnet"""
        return network.Subnet(
            name=self.network_provider.nats_storage_subnet_name,
            resource_name=self.network_provider.nats_storage_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.32.0/24",  # 10.0.32.0 - 10.0.32.255
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_cosmos_subnet(self) -> network.Subnet:
        """Create the Agents subnet"""
        return network.Subnet(
            name=self.network_provider.cosmos_subnet_name,
            resource_name=self.network_provider.cosmos_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.33.0/24",  # 10.0.33.0 - 10.0.33.255
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_search_subnet(self) -> network.Subnet:
        """Create the Agents subnet"""
        return network.Subnet(
            name=self.network_provider.search_subnet_name,
            resource_name=self.network_provider.search_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.34.0/24",  # 10.0.34.0 - 10.0.34.255
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_dagster_storage_subnet(self) -> network.Subnet:
        """Create the Agents subnet"""
        return network.Subnet(
            name=self.network_provider.dagster_storage_subnet_name,
            resource_name=self.network_provider.dagster_storage_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.35.0/24",  # 10.0.35.0 - 10.0.35.255
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _register_outputs(self):
        """Register outputs for this component"""
        outputs = {
            "vnet_id": self.vnet.id,
            "vnet_name": self.vnet.name,
        }

        # Add subnet IDs
        for subnet_key, subnet in self.subnets.items():
            outputs[f"{subnet_key}_subnet_id"] = subnet.id
            outputs[f"{subnet_key}_subnet_name"] = subnet.name

        self.register_outputs(outputs)
