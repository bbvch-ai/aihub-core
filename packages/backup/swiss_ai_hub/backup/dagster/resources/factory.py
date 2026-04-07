from dagster._config.pythonic_config import ConfigurableResourceFactory

from swiss_ai_hub.backup.dagster.resources.backup_settings_resource import BackupSettingsResource
from swiss_ai_hub.backup.dagster.resources.container_discovery_resource import ContainerDiscoveryResource
from swiss_ai_hub.backup.dagster.resources.s3_manager_resource import S3ManagerResource


def backup_resources() -> dict[str, ConfigurableResourceFactory]:
    settings = BackupSettingsResource()
    return {
        "backup_settings": settings,
        "s3_manager": S3ManagerResource(settings=settings),
        "container_discovery": ContainerDiscoveryResource(),
    }
