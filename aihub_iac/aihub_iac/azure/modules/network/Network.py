from typing import Optional

import pulumi
from pulumi_azure_native import network

from aihub_iac.azure.modules.nats.NatsConfig import NatsConfig
from aihub_iac.azure.modules.network.NetworkConfig import NetworkConfig
from aihub_iac.azure.modules.stores.StoresConfig import StoresConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider


class Network(pulumi.ComponentResource):
    """A Pulumi component resource for creating network infrastructure"""

    def __init__(self, stack: str, name: str, config: NetworkConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.stack = stack
        self.config = config
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location, self.config.location_short
        )

        self.vnet = None
        self.subnets = {}

        # Create resources
        self._create_resources()

    def _create_resources(self):
        """Create all network resources"""
        # Create virtual network
        self.vnet = self._create_virtual_network()

        # Create subnets
        self.subnets["app"] = self._create_app_subnet()
        self.subnets["agents"] = self._create_agents_subnet()

        # Export outputs
        self._register_outputs()

    def _create_virtual_network(self) -> network.VirtualNetwork:
        return network.VirtualNetwork(
            virtual_network_name=self.network_provider.v_net_name,
            resource_name=self.network_provider.v_net_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            address_space=network.AddressSpaceArgs(address_prefixes=[self.config.VNET_ADDRESS_SPACE]),
            opts=pulumi.ResourceOptions(parent=self),
            tags={
                "Stack": self.stack,
            },
        )

    def _create_app_subnet(self) -> network.Subnet:
        nsg = self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.network_provider.app_subnet_name,
            source_prefixes=[NatsConfig.NATS_SUBNET_CIDR],
        )

        subnet = network.Subnet(
            name=self.network_provider.app_subnet_name,
            resource_name=self.network_provider.app_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.APP_SUBNET_CIDR,
            delegations=[
                network.DelegationArgs(
                    name="app-delegation",
                    service_name="Microsoft.Web/serverFarms",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
            network_security_group={"id": nsg.id},
        )

        return subnet

    def _create_agents_subnet(self) -> network.Subnet:
        nsg = self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.network_provider.agents_subnet_name,
            source_prefixes=[
                StoresConfig.SEARCH_SUBNET_CIDR,
                StoresConfig.COSMOS_SUBNET_CIDR,
                NatsConfig.NATS_SUBNET_CIDR,
            ],
        )

        subnet = network.Subnet(
            name=self.network_provider.agents_subnet_name,
            resource_name=self.network_provider.agents_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.AGENTS_SUBNET_CIDR,
            delegations=[
                network.DelegationArgs(
                    name="aci-agent-delegation",
                    service_name="Microsoft.ContainerInstance/containerGroups",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
            network_security_group={"id": nsg.id},
        )

        return subnet

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
