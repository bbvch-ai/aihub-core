import pulumi
from pulumi_azure_native import network

from aihub_iac.azure.constants.resources import (
    AI_SEARCH_SERVICE,
    APP_SERVICE,
    CONTAINER_APP,
    CONTAINER_INSTANCE,
    COSMOS,
    POSTGRES,
    STORAGE_ACCOUNT,
    SUB_NET,
    V_NET,
)


class NetworkProvider:
    def __init__(self, resource_group, project_name, location, location_short_name):
        self.resource_group = resource_group
        self.project_name = project_name
        self.location = location
        self.location_short_name = location_short_name

    def create_subnet_nsg(
        self,
        parent: pulumi.Resource,
        stack: str,
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
            resource_group_name=self.resource_group,
            location=self.location,
            security_rules=security_rules,
            id=subnet.id,
            opts=pulumi.ResourceOptions(
                parent=parent,
                replace_on_changes=["security_rules"],
            ),
            tags={
                "Stack": stack,
            },
        )

        return nsg

    def get_subnet(self, subnet_name=None):
        return network.get_subnet_output(
            resource_group_name=self.resource_group,
            virtual_network_name=self.v_net_name,
            subnet_name=subnet_name or self.sub_net_name,
        )

    def get_vnet(self):
        return network.get_virtual_network_output(
            resource_group_name=self.resource_group,
            virtual_network_name=self.v_net_name,
        )

    def get_cap_subnet(self):
        return self.get_subnet(subnet_name=self.cap_subnet_name)

    def get_pg_subnet(self):
        return self.get_subnet(subnet_name=self.pg_subnet_name)

    def get_app_subnet(self):
        return self.get_subnet(subnet_name=self.app_subnet_name)

    def get_phoenix_subnet(self):
        return self.get_subnet(subnet_name=self.phoenix_subnet_name)

    def get_webui_storage_subnet(self):
        return self.get_subnet(subnet_name=self.webui_storage_subnet_name)

    def get_cosmos_subnet(self):
        return self.get_subnet(subnet_name=self.cosmos_subnet_name)

    def get_api_cosmos_subnet(self):
        return self.get_subnet(subnet_name=self.api_cosmos_subnet_name)

    def get_search_subnet(self):
        return self.get_subnet(subnet_name=self.search_subnet_name)

    def get_dagster_subnet(self):
        return self.get_subnet(subnet_name=self.dagster_subnet_name)

    def get_webui_subnet(self):
        return self.get_subnet(subnet_name=self.webui_subnet_name)

    def get_dagster_storage_subnet(self):
        return self.get_subnet(subnet_name=self.dagster_storage_subnet_name)

    def get_agents_subnet(self):
        return self.get_subnet(subnet_name=self.agents_subnet_name)

    @property
    def v_net_name(self):
        return f"{self.project_name}-{V_NET}-{self.location_short_name}"

    @property
    def sub_net_name(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}"

    @property
    def app_subnet_name(self):
        return f"{self.sub_net_name}-{APP_SERVICE}"

    @property
    def phoenix_subnet_name(self):
        return f"{self.app_subnet_name}-phoenix"

    @property
    def pg_subnet_name(self):
        return f"{self.sub_net_name}-{POSTGRES}"

    @property
    def cap_subnet_name(self):
        return f"{self.sub_net_name}-{CONTAINER_APP}"

    @property
    def dagster_subnet_name(self):
        return f"{self.cap_subnet_name}-dagster"

    @property
    def webui_subnet_name(self):
        return f"{self.cap_subnet_name}-webui"

    @property
    def agents_subnet_name(self):
        return f"{self.sub_net_name}-{CONTAINER_INSTANCE}-agents"

    @property
    def webui_storage_subnet_name(self):
        return f"{self.sub_net_name}-{STORAGE_ACCOUNT}-webui"

    @property
    def cosmos_subnet_name(self):
        return f"{self.sub_net_name}-{COSMOS}-store"

    @property
    def api_cosmos_subnet_name(self):
        return f"{self.sub_net_name}-{COSMOS}-api"

    @property
    def search_subnet_name(self):
        return f"{self.sub_net_name}-{AI_SEARCH_SERVICE}-store"

    @property
    def priv_endpoint_subnet_name(self):
        return f"{self.sub_net_name}-priv-endpoint"

    @property
    def dagster_storage_subnet_name(self):
        return f"{self.sub_net_name}-{STORAGE_ACCOUNT}-dagster"
