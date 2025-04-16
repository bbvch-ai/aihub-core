import pulumi
from pulumi_azure_native import network

from aihub_iac.azure.constants.resources import (
    V_NET,
    SUB_NET,
    APP_SERVICE,
    CONTAINER_INSTANCE,
    POSTGRES,
    CONTAINER_APP,
    STORAGE_ACCOUNT,
    COSMOS,
    AI_SEARCH_SERVICE,
)


class NetworkProvider:
    def __init__(self, resource_group, project_name, location_short_name):
        self.resource_group = resource_group
        self.project_name = project_name
        self.location_short_name = location_short_name

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

    def get_nats_subnet(self):
        return self.get_subnet(subnet_name=self.nats_subnet_name)

    def get_cap_subnet(self):
        return self.get_subnet(subnet_name=self.cap_subnet_name)

    def get_pg_subnet(self):
        return self.get_subnet(subnet_name=self.pg_subnet_name)

    def get_app_subnet(self):
        return self.get_subnet(subnet_name=self.app_subnet_name)

    def get_nats_storage_subnet(self):
        return self.get_subnet(subnet_name=self.nats_storage_subnet_name)

    def get_cosmos_subnet(self):
        return self.get_subnet(subnet_name=self.cosmos_subnet_name)

    def get_search_subnet(self):
        return self.get_subnet(subnet_name=self.search_subnet_name)

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
    def pg_subnet_name(self):
        return f"{self.sub_net_name}-{POSTGRES}"

    @property
    def cap_subnet_name(self):
        return f"{self.sub_net_name}-{CONTAINER_APP}"

    @property
    def agents_subnet_name(self):
        return f"{self.sub_net_name}-{CONTAINER_INSTANCE}-agents"

    @property
    def nats_storage_subnet_name(self):
        return f"{self.sub_net_name}-{STORAGE_ACCOUNT}-nats"

    @property
    def cosmos_subnet_name(self):
        return f"{self.sub_net_name}-{COSMOS}-store"

    @property
    def search_subnet_name(self):
        return f"{self.sub_net_name}-{AI_SEARCH_SERVICE}-store"

    @property
    def priv_endpoint_subnet_name(self):
        return f"{self.sub_net_name}-priv-endpoint"

    @property
    def nats_subnet_name(self):
        return f"{self.sub_net_name}-{CONTAINER_INSTANCE}-nats"
