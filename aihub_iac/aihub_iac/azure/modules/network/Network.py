import pulumi
from typing import Dict, Optional

from pulumi_azure_native import network, app, operationalinsights

from aihub_iac.azure.constants.resources import V_NET
from aihub_iac.azure.modules.network.NetworkConfig import NetworkConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider

# Address prefix constants
VNET_ADDRESS_SPACE = "10.0.0.0/16"  # 10.0.0.0 - 10.0.255.255
NATS_SUBNET_PREFIX = "10.0.1.0/29"  # 10.0.1.0 - 10.0.1.7
APP_SUBNET_PREFIX = "10.0.2.0/23"  # 10.0.2.0 - 10.0.3.255
PG_SUBNET_PREFIX = "10.0.4.0/24"  # 10.0.4.0 - 10.0.4.255
PRIVATE_ENDPOINT_SUBNET_PREFIX = "10.0.6.0/24"  # 10.0.6.0 - 10.0.6.255
CAPP_SUBNET_PREFIX = "10.0.8.0/23"  # 10.0.8.0 - 10.0.10.255
AGENTS_SUBNET_PREFIX = "10.0.16.0/20"  # 10.0.16.0 - 10.0.31.255
NATS_STORAGE_SUBNET_PREFIX = "10.0.32.0/24"  # 10.0.32.0 - 10.0.32.255
COSMOS_SUBNET_PREFIX = "10.0.33.0/24"  # 10.0.33.0 - 10.0.33.255
SEARCH_SUBNET_PREFIX = "10.0.34.0/24"  # 10.0.34.0 - 10.0.34.255
DAGSTER_STORAGE_SUBNET_PREFIX = "10.0.35.0/24"  # 10.0.35.0 - 10.0.35.255
PHOENIX_SUBNET_PREFIX = "10.0.36.0/24"  # 10.0.36.0 - 10.0.36.255
API_COSMOS_SUBNET_PREFIX = "10.0.37.0/24"  # 10.0.37.0 - 10.0.37.255
DAGSTER_SUBNET_PREFIX = "10.0.38.0/23"  # 10.0.38.0 - 10.0.39.255
WEBUI_SUBNET_PREFIX = "10.0.40.0/23"  # 10.0.40.0 - 10.0.41.255
WEBUI_STORAGE_SUBNET_PREFIX = "10.0.42.0/24"  # 10.0.40.0 - 10.0.40.255


class Network(pulumi.ComponentResource):
    """A Pulumi component resource for creating network infrastructure"""

    def __init__(self, stack: str, name: str, config: NetworkConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

        # Create configuration from environment or use provided config
        self.name = name
        self.stack = stack
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
        self.subnets["nats_storage"] = self._create_nats_storage_subnet()
        self.subnets["app"] = self._create_app_subnet()
        self.subnets["pg"] = self._create_pg_subnet()
        # self.subnets["private_endpoint"] = self._create_private_endpoint_subnet()
        self.subnets["capp"] = self._create_capp_subnet()
        self.subnets["agents"] = self._create_agents_subnet()
        self.subnets["stores_cosmos"] = self._create_stores_cosmos_subnet()
        self.subnets["search"] = self._create_search_subnet()
        self.subnets["dagster"] = self._create_dagster_subnet()
        self.subnets["dagster_storage"] = self._create_dagster_storage_subnet()
        self.subnets["phoenix"] = self._create_phoenix_subnet()
        self.subnets["api_cosmos"] = self._create_api_cosmos_subnet()
        self.subnets["webui"] = self._create_webui_subnet()
        self.subnets["webui_storage"] = self._create_webui_storage_subnet()

        # Export outputs
        self._register_outputs()

    def _create_virtual_network(self) -> network.VirtualNetwork:
        return network.VirtualNetwork(
            virtual_network_name=self.network_provider.v_net_name,
            resource_name=self.network_provider.v_net_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            address_space=network.AddressSpaceArgs(address_prefixes=[VNET_ADDRESS_SPACE]),
            opts=pulumi.ResourceOptions(parent=self),
            tags={
                "Stack": self.stack,
            },
        )

    def _create_nats_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.nats_subnet_name,
            resource_name=self.network_provider.nats_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=NATS_SUBNET_PREFIX,
            delegations=[
                network.DelegationArgs(
                    name="aci-delegation",
                    service_name="Microsoft.ContainerInstance/containerGroups",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(
            self.network_provider.nats_subnet_name,
            subnet,
            [APP_SUBNET_PREFIX, AGENTS_SUBNET_PREFIX, DAGSTER_SUBNET_PREFIX],
        )
        return subnet

    def _create_app_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.app_subnet_name,
            resource_name=self.network_provider.app_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=APP_SUBNET_PREFIX,
            delegations=[
                network.DelegationArgs(
                    name="app-delegation",
                    service_name="Microsoft.Web/serverFarms",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(self.network_provider.app_subnet_name, subnet, [NATS_SUBNET_PREFIX])
        return subnet

    def _create_pg_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.pg_subnet_name,
            resource_name=self.network_provider.pg_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=PG_SUBNET_PREFIX,
            delegations=[
                network.DelegationArgs(
                    name="postgres-delegation",
                    service_name="Microsoft.DBforPostgreSQL/flexibleServers",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(
            self.network_provider.pg_subnet_name,
            subnet,
            [DAGSTER_SUBNET_PREFIX, PHOENIX_SUBNET_PREFIX],
        )
        return subnet

    def _create_private_endpoint_subnet(self) -> network.Subnet:  # ToDo: Maybe Delete
        return network.Subnet(
            name=self.network_provider.priv_endpoint_subnet_name,
            resource_name=self.network_provider.priv_endpoint_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=PRIVATE_ENDPOINT_SUBNET_PREFIX,  # 10.0.6.0 - 10.0.6.255
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_capp_subnet(self) -> network.Subnet:
        return network.Subnet(
            name=self.network_provider.cap_subnet_name,
            resource_name=self.network_provider.cap_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=CAPP_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

    def _create_agents_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.agents_subnet_name,
            resource_name=self.network_provider.agents_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=AGENTS_SUBNET_PREFIX,
            delegations=[
                network.DelegationArgs(
                    name="aci-agent-delegation",
                    service_name="Microsoft.ContainerInstance/containerGroups",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(
            self.network_provider.agents_subnet_name,
            subnet,
            [SEARCH_SUBNET_PREFIX, COSMOS_SUBNET_PREFIX, NATS_SUBNET_PREFIX],
        )
        return subnet

    def _create_nats_storage_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.nats_storage_subnet_name,
            resource_name=self.network_provider.nats_storage_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=NATS_STORAGE_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

        self._create_subnet_nsg(
            self.network_provider.nats_storage_subnet_name,
            subnet,
            [NATS_SUBNET_PREFIX],
        )
        return subnet

    def _create_stores_cosmos_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.cosmos_subnet_name,
            resource_name=self.network_provider.cosmos_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=COSMOS_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(
            self.network_provider.cosmos_subnet_name, subnet, [AGENTS_SUBNET_PREFIX, DAGSTER_SUBNET_PREFIX]
        )
        return subnet

    def _create_search_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.search_subnet_name,
            resource_name=self.network_provider.search_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=SEARCH_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(
            self.network_provider.search_subnet_name, subnet, [AGENTS_SUBNET_PREFIX, DAGSTER_SUBNET_PREFIX]
        )
        return subnet

    def _create_dagster_storage_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.dagster_storage_subnet_name,
            resource_name=self.network_provider.dagster_storage_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=DAGSTER_STORAGE_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )

        public_access_rules = [
            network.SecurityRuleArgs(
                name="AllowInternetToProxy",
                priority=200,
                direction="Inbound",
                access="Allow",
                protocol="Tcp",
                source_address_prefix="Internet",
                source_port_range="*",
                destination_address_prefix="*",
                destination_port_range="4180",
            )
        ]

        self._create_subnet_nsg(
            self.network_provider.dagster_storage_subnet_name,
            subnet,
            [DAGSTER_SUBNET_PREFIX],
            additional_rules=public_access_rules,
        )
        return subnet

    def _create_phoenix_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.phoenix_subnet_name,
            resource_name=self.network_provider.phoenix_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=PHOENIX_SUBNET_PREFIX,
            delegations=[
                network.DelegationArgs(
                    name="app-delegation",
                    service_name="Microsoft.Web/serverFarms",
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        return subnet

    def _create_dagster_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.dagster_subnet_name,
            resource_name=self.network_provider.dagster_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=DAGSTER_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(
            self.network_provider.dagster_subnet_name,
            subnet,
            [],
        )
        return subnet

    def _create_api_cosmos_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.api_cosmos_subnet_name,
            resource_name=self.network_provider.api_cosmos_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=API_COSMOS_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        public_access_rules = [
            network.SecurityRuleArgs(
                name="AllowVPN1ToProxy",
                priority=200,
                direction="Inbound",
                access="Allow",
                protocol="Tcp",
                source_address_prefix="192.168.35.145/32",
                source_port_range="*",
                destination_address_prefix="*",
                destination_port_range="*",
            )
        ]
        self._create_subnet_nsg(
            self.network_provider.api_cosmos_subnet_name,
            subnet,
            [APP_SUBNET_PREFIX],
            additional_rules=public_access_rules,
        )
        return subnet

    def _create_webui_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.webui_subnet_name,
            resource_name=self.network_provider.webui_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=WEBUI_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(
            self.network_provider.webui_subnet_name,
            subnet,
            [],
        )
        return subnet

    def _create_webui_storage_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.network_provider.webui_storage_subnet_name,
            resource_name=self.network_provider.webui_storage_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=WEBUI_STORAGE_SUBNET_PREFIX,
            opts=pulumi.ResourceOptions(parent=self.vnet),
        )
        self._create_subnet_nsg(self.network_provider.webui_storage_subnet_name, subnet, [NATS_SUBNET_PREFIX])
        return subnet

    def _create_subnet_nsg(
        self,
        subnet_name: str,
        subnet: network.Subnet,
        source_prefixes: list[str],
        additional_rules: list[network.SecurityRuleArgs] = None,
    ) -> network.NetworkSecurityGroup:
        """Create NSG for a subnet that only allows traffic from specific source subnets

        Args:
            subnet: The subnet to create NSG for
            source_prefixes: List of source address prefixes to allow traffic from
        """
        # Create security rules for each source prefix
        security_rules = []
        for idx, prefix in enumerate(source_prefixes):
            security_rules.append(
                network.SecurityRuleArgs(
                    name=f"AllowFromSourceSubnet{idx+1}",
                    priority=100 + idx,  # Increment priority for each rule
                    direction="Inbound",
                    access="Allow",
                    protocol="*",
                    source_address_prefix=prefix,
                    source_port_range="*",
                    destination_address_prefix="*",
                    destination_port_range="*",
                )
            )

        # Add any additional rules provided
        if additional_rules:
            # Start priorities after the source subnet rules
            start_priority = 100 + len(source_prefixes)
            for idx, rule in enumerate(additional_rules):
                # If the rule doesn't have a priority set, assign one
                if not hasattr(rule, "priority") or rule.priority is None:
                    rule.priority = start_priority + idx
                security_rules.append(rule)

        # Add the deny rule at the end
        security_rules.append(
            network.SecurityRuleArgs(
                name="DenyAllInbound",
                priority=4096,
                direction="Inbound",
                access="Deny",
                protocol="*",
                source_address_prefix="*",
                source_port_range="*",
                destination_address_prefix="*",
                destination_port_range="*",
            )
        )

        nsg = network.NetworkSecurityGroup(
            resource_name=f"{subnet_name}-nsg",
            network_security_group_name=f"{subnet_name}-nsg",
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            security_rules=security_rules,
            id=subnet.id,
            opts=pulumi.ResourceOptions(
                parent=self,
                replace_on_changes=["security_rules"],
            ),
            tags={
                "Stack": self.stack,
            },
        )

        return nsg

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
