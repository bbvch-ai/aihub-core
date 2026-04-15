from unittest.mock import MagicMock, patch

import dagster as dg
from dagster import AssetKey

from swiss_ai_hub.backup.dagster.assets.backup_service_factory import backup_service_factory
from swiss_ai_hub.backup.dagster.assets.backup_session_factory import backup_session_factory
from swiss_ai_hub.backup.dagster.resources.backup_settings_resource import BackupSettingsResource
from swiss_ai_hub.backup.dagster.resources.container_discovery_resource import ContainerDiscoveryResource
from swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource import ContainerLifecycleResource
from swiss_ai_hub.backup.dagster.resources.docker_manager_resource import DockerManagerResource
from swiss_ai_hub.backup.dagster.resources.s3_manager_resource import S3ManagerResource
from swiss_ai_hub.backup.models import ServiceStatus


def _resources() -> dict[str, object]:
    settings = BackupSettingsResource()
    docker = DockerManagerResource()
    return {
        "backup_settings": settings,
        "s3_manager": S3ManagerResource(settings=settings),
        "docker_manager": docker,
        "container_lifecycle": ContainerLifecycleResource(docker=docker),
        "container_discovery": ContainerDiscoveryResource(),
    }


@patch("swiss_ai_hub.backup.dagster.resources.container_discovery_resource.ContainerDiscovery")
@patch("swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource.ContainerLifecycleManager")
@patch("swiss_ai_hub.backup.dagster.resources.docker_manager_resource.DockerManager")
@patch("swiss_ai_hub.backup.dagster.resources.s3_manager_resource.S3Manager")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_backup_session_creates_context(
    mock_settings_cls: MagicMock,
    mock_s3_cls: MagicMock,
    mock_docker_cls: MagicMock,
    mock_lifecycle_cls: MagicMock,
    mock_discovery_cls: MagicMock,
) -> None:
    """backup_session asset creates a BackupContext with auto-generated timestamp."""
    mock_s3 = MagicMock()
    mock_s3.count_objects.return_value = 0
    mock_s3.bucket = "backups"
    mock_s3_cls.return_value = mock_s3

    mock_discovery = MagicMock()
    mock_discovery.stop_all_managed.return_value = ["api", "web"]
    mock_discovery_cls.return_value = mock_discovery

    session_key = AssetKey(["backup", "session"])
    session_asset = backup_session_factory(session_key)

    result = dg.materialize([session_asset], resources=_resources())

    assert result.success
    mock_discovery.stop_all_managed.assert_called_once()


@patch("swiss_ai_hub.backup.dagster.assets.backup_service_factory.create_handler")
@patch("swiss_ai_hub.backup.dagster.resources.container_discovery_resource.ContainerDiscovery")
@patch("swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource.ContainerLifecycleManager")
@patch("swiss_ai_hub.backup.dagster.resources.docker_manager_resource.DockerManager")
@patch("swiss_ai_hub.backup.dagster.resources.s3_manager_resource.S3Manager")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_backup_service_succeeds(
    mock_settings_cls: MagicMock,
    mock_s3_cls: MagicMock,
    mock_docker_cls: MagicMock,
    mock_lifecycle_cls: MagicMock,
    mock_discovery_cls: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    """Per-service backup asset calls handler.backup() and succeeds."""
    mock_s3 = MagicMock()
    mock_s3.count_objects.return_value = 0
    mock_s3.bucket = "backups"
    mock_s3_cls.return_value = mock_s3

    mock_discovery = MagicMock()
    mock_discovery.stop_all_managed.return_value = ["api"]
    mock_discovery_cls.return_value = mock_discovery

    mock_handler = MagicMock()
    mock_handler.service_name = "PostgreSQL"
    mock_create_handler.return_value = mock_handler

    session_key = AssetKey(["backup", "session"])
    service_key = AssetKey(["backup", "postgres"])
    session_asset = backup_session_factory(session_key)
    service_asset = backup_service_factory(service_key, session_key, "PostgreSQL", "PostgreSQL backup")

    result = dg.materialize(
        [session_asset, service_asset],
        resources=_resources(),
    )

    assert result.success
    mock_handler.backup.assert_called_once()


@patch("swiss_ai_hub.backup.dagster.assets.backup_service_factory.create_handler")
@patch("swiss_ai_hub.backup.dagster.resources.container_discovery_resource.ContainerDiscovery")
@patch("swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource.ContainerLifecycleManager")
@patch("swiss_ai_hub.backup.dagster.resources.docker_manager_resource.DockerManager")
@patch("swiss_ai_hub.backup.dagster.resources.s3_manager_resource.S3Manager")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_backup_service_captures_failure(
    mock_settings_cls: MagicMock,
    mock_s3_cls: MagicMock,
    mock_docker_cls: MagicMock,
    mock_lifecycle_cls: MagicMock,
    mock_discovery_cls: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    """Per-service backup asset returns FAILED result on exception (never raises)."""
    mock_s3 = MagicMock()
    mock_s3.count_objects.return_value = 0
    mock_s3.bucket = "backups"
    mock_s3_cls.return_value = mock_s3

    mock_discovery = MagicMock()
    mock_discovery.stop_all_managed.return_value = ["api"]
    mock_discovery_cls.return_value = mock_discovery

    mock_handler = MagicMock()
    mock_handler.service_name = "PostgreSQL"
    mock_handler.backup.side_effect = RuntimeError("Connection refused")
    mock_create_handler.return_value = mock_handler

    session_key = AssetKey(["backup", "session"])
    service_key = AssetKey(["backup", "postgres"])
    session_asset = backup_session_factory(session_key)
    service_asset = backup_service_factory(service_key, session_key, "PostgreSQL", "PostgreSQL backup")

    result = dg.materialize(
        [session_asset, service_asset],
        resources=_resources(),
    )

    # Asset succeeds (returns FAILED ServiceResult, doesn't raise)
    assert result.success

    service_result = result.output_for_node("backup__postgres")
    assert service_result.status == ServiceStatus.FAILED
    assert "Connection refused" in (service_result.error or "")
