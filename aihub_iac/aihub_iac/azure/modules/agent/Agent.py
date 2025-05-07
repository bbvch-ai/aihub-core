from typing import Optional, List

import pulumi
import time

from pulumi_azure_native import containerinstance

from aihub_iac.azure.modules.agent.AgentConfig import AgentConfig
from aihub_iac.azure.providers.IdentityProvider import IdentityProvider
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider


class Agent(pulumi.ComponentResource):

    PORT = 8080

    def __init__(
        self,
        stack: str,
        name: str,
        config: AgentConfig,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.stack = stack
        # Create configuration from environment or use provided config
        self.config = config

        # Initialize providers
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location_short
        )

        self.identity_provider = IdentityProvider(
            self.config.resource_group,
            self.config.location,
            self.config.subscription_id,
            self.config.project_name,
            self.config.location_short,
        )

        # Create resources in the right order with proper dependencies
        self._create_resources()

    def _create_resources(self):
        """Create all required resources with proper dependency management"""
        # Step 1: Get networking resources
        self.vnet = self.network_provider.get_vnet()
        self.subnet = self.network_provider.get_agents_subnet()

        # Step 2: Create identity and assign roles
        self.identity = self.identity_provider.create_identity(self.name, self.stack)

        # Step 3: Create the container instance
        self.container_instance = self._create_container_instance()

        # Export important outputs
        self.register_outputs(
            {
                "container_group_id": self.container_instance.id,
                "container_group_name": self.container_instance.name,
                "container_group_ip": self.container_instance.ip_address.apply(lambda ip: ip.ip if ip else None),
            }
        )

    def _create_container_instance(self):
        """Create the container instance with proper configuration"""
        group_name = self.config.container_group_name(self.name)
        deployment_timestamp = str(int(time.time()))

        env_vars = self._get_environment_variables()

        agent_container = containerinstance.ContainerArgs(
            name=self.config.container_instance_name(self.name),
            image=self.config.effective_docker_image,
            resources=containerinstance.ResourceRequirementsArgs(
                requests=containerinstance.ResourceRequestsArgs(
                    cpu=self.config.cpu,
                    memory_in_gb=self.config.memory_in_gb,
                ),
            ),
            ports=[containerinstance.ContainerPortArgs(port=self.PORT)],
            environment_variables=env_vars,
        )

        return containerinstance.ContainerGroup(
            resource_name=group_name,
            container_group_name=group_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            os_type="Linux",
            restart_policy=containerinstance.ContainerGroupRestartPolicy.ALWAYS,
            ip_address=containerinstance.IpAddressArgs(
                type=containerinstance.ContainerGroupIpAddressType.PRIVATE,
                ports=[
                    containerinstance.PortArgs(
                        port=self.PORT, protocol=containerinstance.ContainerGroupNetworkProtocol.TCP
                    ),
                ],
            ),
            containers=[agent_container],
            image_registry_credentials=[
                containerinstance.ImageRegistryCredentialArgs(
                    server="ghcr.io",
                    username=self.config.registry_user,
                    password=self.config.registry_pat,
                )
            ],
            identity=containerinstance.ContainerGroupIdentityArgs(
                type=containerinstance.ResourceIdentityType.USER_ASSIGNED,
                user_assigned_identities=[self.identity.user_identity],
            ),
            subnet_ids=[containerinstance.ContainerGroupSubnetIdArgs(id=self.subnet.id)],
            tags={
                "deploymentTimestamp": deployment_timestamp,
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(
                parent=self,
                replace_on_changes=["containers", "ip_address", "identity", "tags"],
                delete_before_replace=True,
            ),
        )

    def _get_nats_container_group_private_ip(self) -> str:
        container_group = containerinstance.get_container_group(
            container_group_name=self.config.nats_container_group_name,
            resource_group_name=self.config.resource_group,
        )
        if container_group.ip_address is not None and container_group.ip_address.ip is not None:
            return container_group.ip_address.ip
        else:
            raise ValueError(f"No private IP found for container group {container_group.name}")

    def _get_environment_variables(self) -> List[containerinstance.EnvironmentVariableArgs]:
        """Define the environment variables for the container"""
        nats_ip = self._get_nats_container_group_private_ip()
        return [
            containerinstance.EnvironmentVariableArgs(
                name="NATS_ENDPOINT",
                value=f"nats://{nats_ip}:4222",
            ),
            containerinstance.EnvironmentVariableArgs(
                name="REDIS_URL",
                value=f"redis://{nats_ip}:6379",
            ),
            containerinstance.EnvironmentVariableArgs(
                name="PHOENIX_ENDPOINT",
                value=f"https://{self.config.phoenix_service_name}.azurewebsites.net",
            ),
            containerinstance.EnvironmentVariableArgs(
                name="PHOENIX_AUTH_TOKEN",
                value=self.config.phoenix_auth_token,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="AZURE_SUBSCRIPTION_ID",
                value=self.config.subscription_id,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="APP_NAME",
                value=self.config.project_name,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="REGION_SHORT",
                value=self.config.location_short,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="COGNITIVE_SEARCH_NAME",
                value=self.config.effective_ai_search_name,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="COGNITIVE_SEARCH_RESOURCE_GROUP_NAME",
                value=self.config.effective_ai_search_resource_group,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="COSMOS_ACCOUNT_NAME",
                value=self.config.effective_doc_store_cosmos_account_name,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="COSMOS_RESOURCE_GROUP_NAME",
                value=self.config.effective_doc_store_cosmos_resource_group,
            ),
            containerinstance.EnvironmentVariableArgs(
                name="LOG_LEVEL",
                value=self.config.log_level,
            ),
        ]
