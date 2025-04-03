from typing import Optional

import pulumi
from pulumi_azure_native import storage

from aihub_iac.azure.resources.storage.StorageConfig import StorageConfig


class StorageResourceFactory:
    """Factory for creating storage-related resources"""

    def __init__(self, config: StorageConfig):
        self.config = config

    def create_storage_account(
        self,
        service_name: str,
        kind: str = "StorageV2",
        sku_name: str = "Standard_LRS",
        access_tier: storage.AccessTier = storage.AccessTier.HOT,
        is_hns_enabled: bool = True,
    ) -> storage.StorageAccount:
        """
        Create a storage account resource

        Args:
            service_name: Identifier for the service using this storage
            kind: Storage account kind (StorageV2, BlobStorage, etc.)
            sku_name: Storage account SKU (Standard_LRS, Premium_LRS, etc.)
            access_tier: Access tier (Hot, Cool)
            is_hns_enabled: Enable hierarchical namespace

        Returns:
            The created storage account
        """
        account_name = self.config.get_storage_account_name(service_name)

        return storage.StorageAccount(
            resource_name=account_name,
            account_name=account_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            kind=kind,
            sku=storage.SkuArgs(name=sku_name),
            access_tier=access_tier,
            is_hns_enabled=is_hns_enabled,
        )

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
        enabled_protocols: Optional[str] = None,
    ) -> storage.FileShare:
        """
        Create a file share resource

        Args:
            name: Name of the file share
            storage_account: The storage account to create the share in
            quota: Quota in GB
            enabled_protocols: Protocol to use (SMB, NFS)

        Returns:
            The created file share
        """
        file_share_args = {
            "resource_name": name,
            "resource_group_name": self.config.resource_group,
            "account_name": storage_account.name,
            "share_name": name,
            "share_quota": quota,
            "opts": pulumi.ResourceOptions(depends_on=[storage_account]),
        }

        if enabled_protocols:
            file_share_args["enabled_protocols"] = enabled_protocols

        return storage.FileShare(**file_share_args)

    def create_blob_container(
        self, name: str, storage_account: storage.StorageAccount, public_access: Optional[storage.PublicAccess] = None
    ) -> storage.BlobContainer:
        """
        Create a blob container

        Args:
            name: Name of the container
            storage_account: The storage account to create the container in
            public_access: Public access level

        Returns:
            The created blob container
        """
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
