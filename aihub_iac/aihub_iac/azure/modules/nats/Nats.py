import pulumi
from pulumi_azure_native import storage, containerinstance

from aihub_iac.azure.constants.resources import STORAGE_ACCOUNT, APP_SERVICE
from aihub_iac.azure.providers.EnvVariableProvider import EnvVariableProvider
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider


class Nats(pulumi.ComponentResource):
    def __init__(self, stack, name, opts=None):
        super().__init__(f"{stack}:{name}", name, None, opts)
        self.stack = stack
        self.name = name

        self.project_name, self.location, self.location_short, self.resource_group, self.subscription_id = (
            EnvVariableProvider.get_environment_variables()
        )

        self.nats_service_name = f"{self.project_name}-{APP_SERVICE}-{self.location_short}-nats"
        self.redis_service_name = f"{self.project_name}-{APP_SERVICE}-{self.location_short}-redis"

        self.nats_volume = "azurefilevolume"
        self.redis_volume = "azurefilevolumeredis"

        self.nats_image_tag = "7.4.2"
        self.redis_image_tag = "7.4.2"

        self.blob_name = f"{self.project_name}{STORAGE_ACCOUNT}{self.location_short}nats"
        self.blob = self._create_blob()

        self.file_share = self._create_file_share("blob")
        self.file_share_redis = self._create_file_share("redis")

        self.network_provider = NetworkProvider(self.resource_group, self.project_name, self.location_short)

    def _create_blob(self):
        return storage.StorageAccount(
            resource_name=self.blob_name,
            account_name=self.blob_name,
            resource_group_name=self.resource_group,
            location=self.location,
            kind="StorageV2",
            sku=storage.SkuArgs(name="Standard_LRS"),
            access_tier=storage.AccessTier.HOT,
            is_hns_enabled=True,
        )

    def _create_file_share(self, file_share_name):
        return storage.FileShare(
            resource_name=file_share_name,
            resource_group_name=self.resource_group,
            account_name=self.blob.name,
            share_name=file_share_name,
            share_quota=100,  # Quota in GB
            opts=pulumi.ResourceOptions(depends_on=[self.blob]),
        )

    def _create_nats_container_group(self):
        return (
            containerinstance.ContainerArgs(
                name=self.nats_service_name,
                image=f"ghcr.io/bbvch-ai/aihub-core/nats:{self.nats_image_tag}",
                command=["nats-server", "-js", "-m", "8222", "-sd", "/mnt/nats-data"],
                ports=[containerinstance.ContainerPortArgs(port=4222), containerinstance.ContainerPortArgs(port=8222)],
                volume_mounts=[containerinstance.VolumeMountArgs(name=self.nats_volume, mount_path="/mnt/nats-data")],
                resources=containerinstance.ResourceRequirementsArgs(
                    requests=containerinstance.ResourceRequestsArgs(
                        memory_in_gb=4,
                        cpu=2,
                    )
                ),
            ),
        )

    def _create_redis_container_group(self):
        return (
            containerinstance.ContainerArgs(
                name=self.redis_service_name,
                image=f"ghcr.io/bbvch-ai/aihub-core/redis:{self.redis_image_tag}",
                command=["redis-server", "--dir", "/mnt/redis"],
                ports=[containerinstance.ContainerPortArgs(port=6379)],
                volume_mounts=[containerinstance.VolumeMountArgs(name=self.redis_volume, mount_path="/mnt/redis")],
                resources=containerinstance.ResourceRequirementsArgs(
                    requests=containerinstance.ResourceRequestsArgs(
                        memory_in_gb=4,
                        cpu=2,
                    )
                ),
            ),
        )
