from dagster import ConfigurableResource, InitResourceContext

from aihub_backup.docker_client import DockerManager


class DockerManagerResource(ConfigurableResource[DockerManager]):
    def create_resource(self, context: InitResourceContext) -> DockerManager:
        return DockerManager()
