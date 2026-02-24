from unittest.mock import MagicMock, patch

import dagster as dg

from aihub_backup.dagster.assets import create_backup
from aihub_backup.models import BackupMode, BackupSummary, ServiceResult, ServiceStatus


@patch("aihub_backup.dagster.assets.build_orchestrator")
def test_create_backup_succeeds(
    mock_build_orchestrator: MagicMock,
    dagster_resources: dict[str, object],
) -> None:
    """Asset produces MaterializeResult per service on successful backup."""
    mock_orchestrator = MagicMock()
    mock_s3 = MagicMock()
    mock_s3.bucket = "backups"
    mock_build_orchestrator.return_value = (mock_orchestrator, mock_s3)
    mock_orchestrator.run_backup.return_value = BackupSummary(
        timestamp="2026-02-19_02-00-00",
        mode=BackupMode.ONLINE,
        results=[
            ServiceResult(name="PostgreSQL", status=ServiceStatus.SUCCEEDED, duration_seconds=10.0),
            ServiceResult(name="Milvus", status=ServiceStatus.SUCCEEDED, duration_seconds=20.0),
            ServiceResult(name="Neo4j", status=ServiceStatus.SUCCEEDED, duration_seconds=5.0),
            ServiceResult(name="ClickHouse", status=ServiceStatus.SUCCEEDED, duration_seconds=3.0),
            ServiceResult(name="Valkey", status=ServiceStatus.SUCCEEDED, duration_seconds=2.0),
            ServiceResult(name="NATS", status=ServiceStatus.SUCCEEDED, duration_seconds=1.0),
        ],
        total_duration_seconds=41.0,
    )

    result = dg.materialize(
        [create_backup],
        resources=dagster_resources,
        partition_key="2026-02-19",
    )

    assert result.success
    mock_orchestrator.run_backup.assert_called_once()


@patch("aihub_backup.dagster.assets.build_orchestrator")
def test_create_backup_includes_retention_warning_in_metadata(
    mock_build_orchestrator: MagicMock,
    dagster_resources: dict[str, object],
) -> None:
    """When retention cleanup fails, retention_warning appears in asset metadata."""
    mock_orchestrator = MagicMock()
    mock_s3 = MagicMock()
    mock_s3.bucket = "backups"
    mock_build_orchestrator.return_value = (mock_orchestrator, mock_s3)
    mock_orchestrator.run_backup.return_value = BackupSummary(
        timestamp="2026-02-19_02-00-00",
        mode=BackupMode.ONLINE,
        results=[
            ServiceResult(name="PostgreSQL", status=ServiceStatus.SUCCEEDED, duration_seconds=10.0),
            ServiceResult(name="Milvus", status=ServiceStatus.SUCCEEDED, duration_seconds=20.0),
            ServiceResult(name="Neo4j", status=ServiceStatus.SUCCEEDED, duration_seconds=5.0),
            ServiceResult(name="ClickHouse", status=ServiceStatus.SUCCEEDED, duration_seconds=3.0),
            ServiceResult(name="Valkey", status=ServiceStatus.SUCCEEDED, duration_seconds=2.0),
            ServiceResult(name="NATS", status=ServiceStatus.SUCCEEDED, duration_seconds=1.0),
        ],
        total_duration_seconds=41.0,
        retention_warning="S3 timeout during cleanup",
    )

    result = dg.materialize(
        [create_backup],
        resources=dagster_resources,
        partition_key="2026-02-19",
    )

    assert result.success
    events = result.get_asset_materialization_events()
    for event in events:
        metadata = event.step_materialization_data.materialization.metadata
        assert "retention_warning" in metadata
        assert metadata["retention_warning"].value == "S3 timeout during cleanup"


@patch("aihub_backup.dagster.assets.build_orchestrator")
def test_create_backup_fails_on_service_failure(
    mock_build_orchestrator: MagicMock,
    dagster_resources: dict[str, object],
) -> None:
    """Asset raises Failure when a service backup fails."""
    mock_orchestrator = MagicMock()
    mock_s3 = MagicMock()
    mock_s3.bucket = "backups"
    mock_build_orchestrator.return_value = (mock_orchestrator, mock_s3)
    mock_orchestrator.run_backup.return_value = BackupSummary(
        timestamp="2026-02-19_02-00-00",
        mode=BackupMode.ONLINE,
        results=[
            ServiceResult(name="PostgreSQL", status=ServiceStatus.SUCCEEDED, duration_seconds=10.0),
            ServiceResult(name="Milvus", status=ServiceStatus.FAILED, duration_seconds=0.0, error="Connection refused"),
            ServiceResult(name="Neo4j", status=ServiceStatus.SUCCEEDED, duration_seconds=5.0),
            ServiceResult(name="ClickHouse", status=ServiceStatus.SUCCEEDED, duration_seconds=3.0),
            ServiceResult(name="Valkey", status=ServiceStatus.SUCCEEDED, duration_seconds=2.0),
            ServiceResult(name="NATS", status=ServiceStatus.SUCCEEDED, duration_seconds=1.0),
        ],
        total_duration_seconds=21.0,
    )

    result = dg.materialize(
        [create_backup],
        resources=dagster_resources,
        partition_key="2026-02-19",
        raise_on_error=False,
    )

    assert not result.success
