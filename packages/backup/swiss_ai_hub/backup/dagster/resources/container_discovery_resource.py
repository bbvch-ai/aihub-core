from dagster import ConfigurableResource, InitResourceContext

from swiss_ai_hub.backup.container_discovery import ContainerDiscovery


class ContainerDiscoveryResource(ConfigurableResource[ContainerDiscovery]):
    def create_resource(self, context: InitResourceContext) -> ContainerDiscovery:
        return ContainerDiscovery()
