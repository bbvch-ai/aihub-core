from swiss_ai_hub.backup.dagster.resources.backup_settings_resource import BackupSettingsResource
from swiss_ai_hub.backup.dagster.resources.container_discovery_resource import ContainerDiscoveryResource
from swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource import ContainerLifecycleResource
from swiss_ai_hub.backup.dagster.resources.docker_manager_resource import DockerManagerResource
from swiss_ai_hub.backup.dagster.resources.s3_manager_resource import S3ManagerResource


def backup_resources() -> dict[str, object]:
    settings = BackupSettingsResource()
    docker = DockerManagerResource()
    return {
        "backup_settings": settings,
        "s3_manager": S3ManagerResource(settings=settings),
        "docker_manager": docker,
        "container_lifecycle": ContainerLifecycleResource(docker=docker),
        "container_discovery": ContainerDiscoveryResource(),
    }
