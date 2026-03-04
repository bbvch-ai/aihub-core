from dagster._config.pythonic_config import ConfigurableResourceFactory

from aihub_backup.dagster.resources.BackupSettingsResource import BackupSettingsResource
from aihub_backup.dagster.resources.ContainerDiscoveryResource import ContainerDiscoveryResource
from aihub_backup.dagster.resources.ContainerLifecycleResource import ContainerLifecycleResource
from aihub_backup.dagster.resources.DockerManagerResource import DockerManagerResource
from aihub_backup.dagster.resources.S3ManagerResource import S3ManagerResource


def backup_resources() -> dict[str, ConfigurableResourceFactory]:
    settings = BackupSettingsResource()
    docker = DockerManagerResource()
    return {
        "backup_settings": settings,
        "s3_manager": S3ManagerResource(settings=settings),
        "docker_manager": docker,
        "container_lifecycle": ContainerLifecycleResource(docker=docker),
        "container_discovery": ContainerDiscoveryResource(),
    }
