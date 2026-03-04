from dagster import ConfigurableResource, InitResourceContext, ResourceDependency

from aihub_backup.container_lifecycle import ContainerLifecycleManager
from aihub_backup.docker_client import DockerManager


class ContainerLifecycleResource(ConfigurableResource[ContainerLifecycleManager]):
    docker: ResourceDependency[DockerManager]

    def create_resource(self, context: InitResourceContext) -> ContainerLifecycleManager:
        return ContainerLifecycleManager(self.docker)
