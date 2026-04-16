from unittest.mock import MagicMock, patch

import dagster as dg
from dagster import AssetKey, DagsterInstance

from swiss_ai_hub.backup.dagster.assets.restore_finalize_factory import restore_finalize_factory
from swiss_ai_hub.backup.dagster.assets.restore_service_factory import restore_service_factory
from swiss_ai_hub.backup.dagster.assets.restore_session_factory import restore_session_factory
from swiss_ai_hub.backup.dagster.partitions import backup_partitions
from swiss_ai_hub.backup.dagster.resources.backup_settings_resource import BackupSettingsResource
from swiss_ai_hub.backup.dagster.resources.container_discovery_resource import ContainerDiscoveryResource
from swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource import ContainerLifecycleResource
from swiss_ai_hub.backup.dagster.resources.docker_manager_resource import DockerManagerResource
from swiss_ai_hub.backup.dagster.resources.s3_manager_resource import S3ManagerResource

import pytest

_TIMESTAMP = "2026-02-19_02-00-00"


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


def _build_restore_assets() -> list[dg.AssetsDefinition]:
    session_key = AssetKey(["restore", "session"])
    service_keys = {
        "PostgreSQL": AssetKey(["restore", "postgres"]),
        "Milvus": AssetKey(["restore", "milvus"]),
        "Neo4j": AssetKey(["restore", "neo4j"]),
        "ClickHouse": AssetKey(["restore", "clickhouse"]),
        "Valkey": AssetKey(["restore", "valkey"]),
        "NATS": AssetKey(["restore", "nats"]),
    }
    finalize_key = AssetKey(["restore", "finalize"])

    session = restore_session_factory(session_key)
    service_assets = [
        restore_service_factory(key, session_key, name, f"{name} restore") for name, key in service_keys.items()
    ]
    finalize = restore_finalize_factory(finalize_key, session_key, service_keys)
    return [session, *service_assets, finalize]


def _instance_with_partition() -> DagsterInstance:
    instance = DagsterInstance.ephemeral()
    instance.add_dynamic_partitions(backup_partitions.name, [_TIMESTAMP])
    return instance


@patch("swiss_ai_hub.backup.dagster.assets.restore_service_factory.create_handler")
@patch("swiss_ai_hub.backup.dagster.assets.restore_session_factory._validate_backup_completeness_or_raise")
@patch("swiss_ai_hub.backup.dagster.resources.container_discovery_resource.ContainerDiscovery")
@patch("swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource.ContainerLifecycleManager")
@patch("swiss_ai_hub.backup.dagster.resources.docker_manager_resource.DockerManager")
@patch("swiss_ai_hub.backup.dagster.resources.s3_manager_resource.S3Manager")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_full_restore_succeeds(
    mock_settings_cls: MagicMock,
    mock_s3_cls: MagicMock,
    mock_docker_cls: MagicMock,
    mock_lifecycle_cls: MagicMock,
    mock_discovery_cls: MagicMock,
    mock_validate: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    """Full restore completes all services successfully."""
    mock_lifecycle = MagicMock()
    mock_lifecycle_cls.return_value = mock_lifecycle
    mock_s3 = MagicMock()
    mock_s3.resolve_timestamp.return_value = _TIMESTAMP
    mock_s3_cls.return_value = mock_s3

    mock_discovery = MagicMock()
    mock_discovery.discover_managed_containers.return_value = ["api", "web", "postgres"]
    mock_discovery_cls.return_value = mock_discovery

    mock_handler = MagicMock()
    mock_handler.service_name = "TestService"
    mock_create_handler.return_value = mock_handler

    result = dg.materialize(
        _build_restore_assets(),
        resources=_resources(),
        instance=_instance_with_partition(),
        partition_key=_TIMESTAMP,
    )

    assert result.success
    mock_discovery.stop_all_managed.assert_called_once()
    mock_discovery.start_all.assert_called_once()


@patch("swiss_ai_hub.backup.dagster.assets.restore_service_factory.create_handler")
@patch("swiss_ai_hub.backup.dagster.assets.restore_session_factory._validate_backup_completeness_or_raise")
@patch("swiss_ai_hub.backup.dagster.resources.container_discovery_resource.ContainerDiscovery")
@patch("swiss_ai_hub.backup.dagster.resources.container_lifecycle_resource.ContainerLifecycleManager")
@patch("swiss_ai_hub.backup.dagster.resources.docker_manager_resource.DockerManager")
@patch("swiss_ai_hub.backup.dagster.resources.s3_manager_resource.S3Manager")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_full_restore_fails_on_service_error(
    mock_settings_cls: MagicMock,
    mock_s3_cls: MagicMock,
    mock_docker_cls: MagicMock,
    mock_lifecycle_cls: MagicMock,
    mock_discovery_cls: MagicMock,
    mock_validate: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    """Restore fails catastrophically — no container restart, no recovery."""
    mock_lifecycle = MagicMock()
    mock_lifecycle_cls.return_value = mock_lifecycle
    mock_s3 = MagicMock()
    mock_s3.resolve_timestamp.return_value = _TIMESTAMP
    mock_s3_cls.return_value = mock_s3

    mock_discovery = MagicMock()
    mock_discovery.discover_managed_containers.return_value = ["api", "web"]
    mock_discovery_cls.return_value = mock_discovery

    mock_handler = MagicMock()
    mock_handler.service_name = "PostgreSQL"
    mock_handler.restore.side_effect = RuntimeError("pg_restore failed")
    mock_create_handler.return_value = mock_handler

    result = dg.materialize(
        _build_restore_assets(),
        resources=_resources(),
        instance=_instance_with_partition(),
        partition_key=_TIMESTAMP,
        raise_on_error=False,
    )

    assert not result.success
    mock_discovery.start_all.assert_not_called()
