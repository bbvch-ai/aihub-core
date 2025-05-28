from typing import Dict

import pulumi
from pulumi_azure_native import network, privatedns

from aihub_iac.azure.providers.NetworkProvider import NetworkProvider


class PrivateEndpointProvider:
    """Manages the creation of private endpoints and related resources."""

    def __init__(
        self,
        resource_group: str,
        location: str,
        network_provider: NetworkProvider,
        stack: str,
        parent: pulumi.Resource = None,
    ):
        self.resource_group = resource_group
        self.location = location
        self.network_provider = network_provider
        self.parent = parent
        self.dns_zones: Dict[str, privatedns.PrivateZone] = {}
        self.vnet_links: Dict[str, privatedns.VirtualNetworkLink] = {}
        self.stack = stack

    def create_dns_zone(self, zone_name: str, zone_domain: str) -> privatedns.PrivateZone:
        """Create a private DNS zone and associated virtual network link."""
        dns_zone = privatedns.PrivateZone(
            resource_name=f"{zone_name}-dns-zone",
            private_zone_name=zone_domain,
            resource_group_name=self.resource_group,
            location="Global",
            opts=pulumi.ResourceOptions(parent=self.parent),
            tags={
                "Stack": self.stack,
            },
        )

        vnet_link = privatedns.VirtualNetworkLink(
            resource_name=f"{zone_name}-vnet-link",
            virtual_network_link_name=f"{zone_name}-vnet-link",
            private_zone_name=dns_zone.name,
            resource_group_name=self.resource_group,
            virtual_network=network.SubResourceArgs(
                id=self.network_provider.get_vnet().id,
            ),
            registration_enabled=False,
            location="Global",
            opts=pulumi.ResourceOptions(parent=self.parent, depends_on=[dns_zone]),
            tags={
                "Stack": self.stack,
            },
        )

        self.dns_zones[zone_name] = dns_zone
        self.vnet_links[zone_name] = vnet_link

        return dns_zone

    def create_private_endpoint(
        self,
        name: str,
        resource_id: pulumi.Output,
        subnet_id: pulumi.Output,
        group_id: str,
        dns_zone: privatedns.PrivateZone,
        depends_on=None,
    ) -> network.PrivateEndpoint:
        """Create a private endpoint with DNS zone group."""
        # Create private endpoint
        private_endpoint = network.PrivateEndpoint(
            resource_name=f"{name}-pe",
            private_endpoint_name=f"{name}-pe",
            resource_group_name=self.resource_group,
            location=self.location,
            subnet=network.SubnetArgs(id=subnet_id),
            private_link_service_connections=[
                network.PrivateLinkServiceConnectionArgs(
                    name=f"{name}-{group_id}-privatelink",
                    private_link_service_id=resource_id,
                    group_ids=[group_id],
                )
            ],
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self.parent, depends_on=depends_on or []),
        )

        # Create DNS zone group
        network.PrivateDnsZoneGroup(
            resource_name=f"{name}-dns-group",
            private_dns_zone_group_name="default",
            private_endpoint_name=private_endpoint.name,
            resource_group_name=self.resource_group,
            private_dns_zone_configs=[
                network.PrivateDnsZoneConfigArgs(
                    name="config1",
                    private_dns_zone_id=dns_zone.id,
                )
            ],
            opts=pulumi.ResourceOptions(parent=self.parent, depends_on=[private_endpoint, dns_zone]),
        )

        return private_endpoint
