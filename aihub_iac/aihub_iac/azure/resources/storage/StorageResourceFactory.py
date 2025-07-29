import pulumi
from pulumi_azure_native import network, privatedns, storage

from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig


class StorageResourceFactory:
    """Factory for creating storage-related resources"""

    def __init__(self, config: StorageConfig, stack: str):
        self.config = config
        self.stack = stack

    def create_storage_account(
        self,
        service_name: str,
        subnet_id: str,
        vnet_id: str,
        kind: str = "StorageV2",
        sku_name: str = "Standard_LRS",
        access_tier: storage.AccessTier = storage.AccessTier.HOT,
        is_hns_enabled: bool = True,
        network_rule_set: storage.NetworkRuleSetArgs | None = None,
        blob_only: bool = False,
        existing_blob_dns_zone: privatedns.GetPrivateZoneResult | None = None,
        existing_file_dns_zone: privatedns.GetPrivateZoneResult | None = None,
    ) -> storage.StorageAccount:
        """Create a storage account resource."""
        account_name = self.config.get_storage_account_name(service_name)

        # Set up arguments for storage account
        storage_args = {
            "resource_name": account_name,
            "account_name": account_name,
            "resource_group_name": self.config.resource_group,
            "location": self.config.location,
            "kind": kind,
            "sku": storage.SkuArgs(name=sku_name),
            "access_tier": access_tier,
            "is_hns_enabled": is_hns_enabled,
            "tags": {
                "Stack": self.stack,
            },
        }

        # Add network rules if provided (for service endpoints)
        if network_rule_set:
            storage_args["network_rule_set"] = network_rule_set

        # Create the storage account
        storage_account = storage.StorageAccount(**storage_args)

        # Create a private endpoint for the blob service
        if not existing_blob_dns_zone:
            blob_dns_zone = self._create_blob_dns_zone(vnet_id)
            dns_zone_id = blob_dns_zone.id
        else:
            dns_zone_id = existing_blob_dns_zone.id

        # Create private endpoint for blob service
        self._create_storage_private_endpoint(
            account_name=account_name,
            storage_account=storage_account,
            subnet_id=subnet_id,
            dns_zone_id=dns_zone_id,
            group_id="blob",
        )

        # For file shares, create a private endpoint for the file service
        if kind in ["StorageV2", "FileStorage"] and not blob_only:
            if not existing_file_dns_zone:
                file_dns_zone = self._create_file_dns_zone(vnet_id)
                dns_zone_id = file_dns_zone.id
            else:
                dns_zone_id = existing_file_dns_zone.id

            self._create_storage_private_endpoint(
                account_name=account_name,
                storage_account=storage_account,
                subnet_id=subnet_id,
                dns_zone_id=dns_zone_id,
                group_id="file",
            )

        return storage_account

    def _create_storage_private_endpoint(
        self,
        account_name: str,
        storage_account: storage.StorageAccount,
        subnet_id: str,
        dns_zone_id: pulumi.Input[str] | None = None,
        group_id: str = "blob",
    ) -> network.PrivateEndpoint:
        """Create a private endpoint for a storage service."""
        pe_name = f"{account_name}-{group_id}-pe"

        private_endpoint = network.PrivateEndpoint(
            resource_name=pe_name,
            private_endpoint_name=pe_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            subnet=network.SubnetArgs(id=subnet_id),
            private_link_service_connections=[
                network.PrivateLinkServiceConnectionArgs(
                    name=f"{account_name}-{group_id}-privatelink",
                    group_ids=[group_id],
                    private_link_service_id=storage_account.id,
                )
            ],
            tags={
                "Stack": self.stack,
            },
        )

        network.PrivateDnsZoneGroup(
            resource_name=f"{pe_name}-dns-zone-group",
            resource_group_name=self.config.resource_group,
            private_endpoint_name=private_endpoint.name,
            private_dns_zone_group_name="default",
            private_dns_zone_configs=[
                network.PrivateDnsZoneConfigArgs(name="config1", private_dns_zone_id=dns_zone_id)
            ],
        )
        return private_endpoint

    def _create_blob_dns_zone(self, vnet_id: str):
        blob_dns_zone = privatedns.PrivateZone(
            "blob-dns-zone",
            resource_group_name=self.config.resource_group,
            private_zone_name="privatelink.blob.core.windows.net",
            location="Global",
        )
        privatedns.VirtualNetworkLink(
            "blob-zone-link",
            resource_group_name=self.config.resource_group,
            private_zone_name=blob_dns_zone.name,
            virtual_network=network.SubResourceArgs(id=vnet_id),
            registration_enabled=False,
            location="Global",
            opts=pulumi.ResourceOptions(parent=blob_dns_zone),
        )
        return blob_dns_zone

    def _create_file_dns_zone(self, vnet_id: str):
        file_dns_zone = privatedns.PrivateZone(
            "file-dns-zone",
            resource_group_name=self.config.resource_group,
            private_zone_name="privatelink.file.core.windows.net",
            location="Global",
        )
        privatedns.VirtualNetworkLink(
            "file-zone-link",
            resource_group_name=self.config.resource_group,
            private_zone_name=file_dns_zone.name,
            virtual_network=network.SubResourceArgs(id=vnet_id),
            registration_enabled=False,
            location="Global",
            opts=pulumi.ResourceOptions(parent=file_dns_zone),
        )
        return file_dns_zone

    def get_storage_account_key(self, storage_account: storage.StorageAccount) -> pulumi.Output:
        """Get the storage account key"""
        storage_account_keys = pulumi.Output.all(storage_account.name, self.config.resource_group).apply(
            lambda args: storage.list_storage_account_keys(resource_group_name=args[1], account_name=args[0])
        )
        return storage_account_keys.keys[0].value

    def create_file_share(
        self,
        name: str,
        storage_account: storage.StorageAccount,
        quota: int = 100,
        enabled_protocols: str | None = None,
    ) -> storage.FileShare:
        """Create a file share resource."""
        account_name = pulumi.Output.all(storage_account.name, storage_account.provisioning_state).apply(
            lambda args: args[0]
        )

        # Create file share args
        file_share_args = {
            "resource_name": name,
            "resource_group_name": self.config.resource_group,
            "account_name": account_name,
            "share_name": name,
            "share_quota": quota,
            "opts": pulumi.ResourceOptions(depends_on=[storage_account]),
        }

        if enabled_protocols:
            file_share_args["enabled_protocols"] = enabled_protocols

        return storage.FileShare(**file_share_args)

    def create_blob_container(
        self, name: str, storage_account: storage.StorageAccount, public_access: storage.PublicAccess | None = None
    ) -> storage.BlobContainer:
        """Create a blob container."""
        container_args = {
            "resource_name": name,
            "resource_group_name": self.config.resource_group,
            "account_name": storage_account.name,
            "container_name": name,
            "opts": pulumi.ResourceOptions(depends_on=[storage_account]),
        }

        if public_access:
            container_args["public_access"] = public_access

        return storage.BlobContainer(**container_args)
