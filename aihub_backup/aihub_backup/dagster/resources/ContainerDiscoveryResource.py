from dagster import ConfigurableResource, InitResourceContext

from aihub_backup.container_discovery import ContainerDiscovery


class ContainerDiscoveryResource(ConfigurableResource[ContainerDiscovery]):
    def create_resource(self, context: InitResourceContext) -> ContainerDiscovery:
        return ContainerDiscovery()
