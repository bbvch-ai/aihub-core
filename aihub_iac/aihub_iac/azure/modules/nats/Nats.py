from typing import Optional

import pulumi
from pulumi_azure_native import containerinstance

from aihub_iac.azure.modules.nats.NatsConfig import NatsConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.resources.storage.StorageResourceFactory import StorageResourceFactory


class Nats(pulumi.ComponentResource):
    """A Pulumi component resource for deploying NATS and Redis services

    # Example Usage:
    config = NatsConfig.from_env(stack="Nats", name="nats", nats_image_tag="1.2.3", redis_image_tag="1.2.3")
    Nats(stack, name, config=config)
    """

    def __init__(self, stack: str, name: str, config: NatsConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.stack = stack
        self.config = config
        self.storage_factory = StorageResourceFactory(self.config, self.stack)
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location_short
        )
        self._create_resources()

    def _create_nats_container(self) -> containerinstance.ContainerArgs:
        """Create a NATS container configuration"""
        return containerinstance.ContainerArgs(
            name=self.config.nats_service_name,
            image=f"ghcr.io/bbvch-ai/aihub-core/nats:{self.config.nats_image_tag}",
            command=["nats-server", "-js", "-m", "8222", "-sd", "/mnt/nats-data"],
            ports=[containerinstance.ContainerPortArgs(port=4222), containerinstance.ContainerPortArgs(port=8222)],
            volume_mounts=[
                containerinstance.VolumeMountArgs(name=self.config.nats_volume, mount_path="/mnt/nats-data")
            ],
            resources=containerinstance.ResourceRequirementsArgs(
                requests=containerinstance.ResourceRequestsArgs(
                    memory_in_gb=self.config.nats_memory,
                    cpu=self.config.nats_cpu,
                )
            ),
        )

    def _create_redis_container(self) -> containerinstance.ContainerArgs:
        """Create a Redis container configuration"""
        return containerinstance.ContainerArgs(
            name=self.config.redis_service_name,
            image=f"ghcr.io/bbvch-ai/aihub-core/redis:{self.config.redis_image_tag}",
            command=["redis-server", "--dir", "/mnt/redis"],
            ports=[containerinstance.ContainerPortArgs(port=6379)],
            volume_mounts=[containerinstance.VolumeMountArgs(name=self.config.redis_volume, mount_path="/mnt/redis")],
            resources=containerinstance.ResourceRequirementsArgs(
                requests=containerinstance.ResourceRequestsArgs(
                    memory_in_gb=self.config.redis_memory,
                    cpu=self.config.redis_cpu,
                )
            ),
        )

    def _create_resources(self):
        """Create all required resources with proper dependency management"""
        self.vnet = self.network_provider.get_vnet()
        self.nats_storage_subnet = self.network_provider.get_nats_storage_subnet()
        self.nats_subnet = self.network_provider.get_nats_subnet()

        self.storage_account = self.storage_factory.create_storage_account(
            service_name=self.config.storage_service_name,
            subnet_id=self.nats_storage_subnet.id,
            vnet_id=self.vnet.id,
        )
        self.storage_account_key = self.storage_factory.get_storage_account_key(self.storage_account)

        self.nats_file_share = self.storage_factory.create_file_share("blob", self.storage_account)
        self.redis_file_share = self.storage_factory.create_file_share("redis", self.storage_account)

        self.nats_container = self._create_nats_container()
        self.redis_container = self._create_redis_container()

        self.container_group = self._create_container_group()

        # Export important outputs
        self.register_outputs(
            {
                "container_group_id": self.container_group.id,
                "storage_account_id": self.storage_account.id,
                "nats_service_name": self.config.nats_service_name,
                "redis_service_name": self.config.redis_service_name,
            }
        )

    def _create_container_group(self) -> containerinstance.ContainerGroup:
        """Create the container group with all required resources"""
        # Validate that all required resources exist
        required_resources = [
            ("storage_account", self.storage_account),
            ("storage_account_key", self.storage_account_key),
            ("nats_file_share", self.nats_file_share),
            ("redis_file_share", self.redis_file_share),
            ("nats_container", self.nats_container),
            ("redis_container", self.redis_container),
            ("network_provider", self.network_provider),
        ]

        missing = [name for name, resource in required_resources if resource is None]
        if missing:
            raise ValueError(f"Missing required resources: {', '.join(missing)}")

        return containerinstance.ContainerGroup(
            resource_name=self.config.container_instance_name,
            container_group_name=self.config.container_instance_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            os_type="Linux",
            restart_policy=containerinstance.ContainerGroupRestartPolicy.ALWAYS,
            ip_address=containerinstance.IpAddressArgs(
                type=containerinstance.ContainerGroupIpAddressType.PRIVATE,
                ports=[
                    containerinstance.PortArgs(port=4222, protocol=containerinstance.ContainerGroupNetworkProtocol.TCP),
                    containerinstance.PortArgs(port=8222, protocol=containerinstance.ContainerGroupNetworkProtocol.TCP),
                    containerinstance.PortArgs(port=6379, protocol=containerinstance.ContainerGroupNetworkProtocol.TCP),
                ],
            ),
            containers=[self.nats_container, self.redis_container],
            image_registry_credentials=[
                containerinstance.ImageRegistryCredentialArgs(
                    server="ghcr.io", username=self.config.registry_user, password=self.config.registry_pat
                )
            ],
            volumes=[
                containerinstance.VolumeArgs(
                    name=self.config.nats_volume,
                    azure_file=containerinstance.AzureFileVolumeArgs(
                        share_name=self.nats_file_share.name,
                        storage_account_name=self.storage_account.name,
                        storage_account_key=self.storage_account_key,
                    ),
                ),
                containerinstance.VolumeArgs(
                    name=self.config.redis_volume,
                    azure_file=containerinstance.AzureFileVolumeArgs(
                        share_name=self.redis_file_share.name,
                        storage_account_name=self.storage_account.name,
                        storage_account_key=self.storage_account_key,
                    ),
                ),
            ],
            identity=containerinstance.ContainerGroupIdentityArgs(
                type=containerinstance.ResourceIdentityType.SYSTEM_ASSIGNED
            ),
            subnet_ids=[containerinstance.ContainerGroupSubnetIdArgs(id=self.nats_subnet.id)],
            opts=pulumi.ResourceOptions(
                replace_on_changes=["containers", "volumes"],
                delete_before_replace=True,
            ),
            tags={"Stack": self.stack},
        )
