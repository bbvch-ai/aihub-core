from dagster import ConfigurableResource, InitResourceContext, ResourceDependency

from swiss_ai_hub.backup.container_lifecycle import ContainerLifecycleManager
from swiss_ai_hub.backup.docker_client import DockerManager


class ContainerLifecycleResource(ConfigurableResource[ContainerLifecycleManager]):
    docker: ResourceDependency[DockerManager]

    def create_resource(self, context: InitResourceContext) -> ContainerLifecycleManager:
        return ContainerLifecycleManager(self.docker)
