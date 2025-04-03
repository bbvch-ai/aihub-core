import pulumi
from pulumi_azure_native import network

from aihub_iac.azure.constants.resources import V_NET, SUB_NET, APP_SERVICE, CONTAINER_INSTANCE


class NetworkProvider:
    def __init__(self, resource_group, project_name, location_short_name):
        self.resource_group = resource_group
        self.project_name = project_name
        self.location_short_name = location_short_name
        self.v_net_name = f"{self.project_name}-{V_NET}-{self.location_short_name}"
        self.sub_net_name = f"{self.project_name}-{SUB_NET}-{self.location_short_name}"

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

    @property
    def app_subnet(self):
        return f"{self.sub_net_name}-{APP_SERVICE}"

    @property
    def nats_subnet(self):
        return self.get_subnet(f"{self.sub_net_name}-{CONTAINER_INSTANCE}-nats")
