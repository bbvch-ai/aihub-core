from unittest.mock import MagicMock, patch

from dagster import RunConfig

from aihub_backup.dagster.jobs import full_restore_job, single_service_restore_job
from aihub_backup.models import BackupMode, BackupSummary, ServiceResult, ServiceStatus


def _restore_run_config(timestamp: str = "2026-02-19_02-00-00") -> RunConfig:
    return RunConfig(ops={"run_full_restore": {"config": {"timestamp": timestamp}}})


def _single_restore_run_config(service_name: str, timestamp: str = "2026-02-19_02-00-00") -> RunConfig:
    return RunConfig(
        ops={"run_single_service_restore": {"config": {"service_name": service_name, "timestamp": timestamp}}}
    )


@patch("aihub_backup.dagster.ops.restore_ops.build_orchestrator")
def test_full_restore_succeeds(
    mock_build_orchestrator: MagicMock,
    dagster_resources: dict[str, object],
) -> None:
    """Full restore job completes successfully."""
    mock_orchestrator = MagicMock()
    mock_s3 = MagicMock()
    mock_build_orchestrator.return_value = (mock_orchestrator, mock_s3)
    mock_orchestrator.run_restore.return_value = BackupSummary(
        timestamp="2026-02-19_02-00-00_online",
        mode=BackupMode.ONLINE,
        results=[
            ServiceResult(name="PostgreSQL", status=ServiceStatus.SUCCEEDED, duration_seconds=30.0),
            ServiceResult(name="Neo4j", status=ServiceStatus.SUCCEEDED, duration_seconds=10.0),
            ServiceResult(name="ClickHouse", status=ServiceStatus.SUCCEEDED, duration_seconds=5.0),
            ServiceResult(name="Milvus", status=ServiceStatus.SUCCEEDED, duration_seconds=15.0),
        ],
        total_duration_seconds=60.0,
    )

    result = full_restore_job.execute_in_process(
        resources=dagster_resources,
        run_config=_restore_run_config(),
    )

    assert result.success
    mock_orchestrator.run_restore.assert_called_once()


@patch("aihub_backup.dagster.ops.restore_ops.build_orchestrator")
def test_full_restore_fails_on_service_failure(
    mock_build_orchestrator: MagicMock,
    dagster_resources: dict[str, object],
) -> None:
    """Full restore job fails when a service restore fails."""
    mock_orchestrator = MagicMock()
    mock_s3 = MagicMock()
    mock_build_orchestrator.return_value = (mock_orchestrator, mock_s3)
    mock_orchestrator.run_restore.return_value = BackupSummary(
        timestamp="2026-02-19_02-00-00_online",
        mode=BackupMode.ONLINE,
        results=[
            ServiceResult(name="PostgreSQL", status=ServiceStatus.FAILED, duration_seconds=5.0, error="DB error"),
            ServiceResult(name="Neo4j", status=ServiceStatus.SUCCEEDED, duration_seconds=10.0),
            ServiceResult(name="ClickHouse", status=ServiceStatus.SUCCEEDED, duration_seconds=5.0),
            ServiceResult(name="Milvus", status=ServiceStatus.SUCCEEDED, duration_seconds=15.0),
        ],
        total_duration_seconds=35.0,
    )

    result = full_restore_job.execute_in_process(
        resources=dagster_resources,
        run_config=_restore_run_config(),
        raise_on_error=False,
    )

    assert not result.success


@patch("aihub_backup.dagster.ops.restore_ops.build_orchestrator")
def test_single_service_restore_succeeds(
    mock_build_orchestrator: MagicMock,
    dagster_resources: dict[str, object],
) -> None:
    """Single service restore job completes successfully."""
    mock_orchestrator = MagicMock()
    mock_s3 = MagicMock()
    mock_build_orchestrator.return_value = (mock_orchestrator, mock_s3)
    mock_orchestrator.run_single_restore.return_value = ServiceResult(
        name="PostgreSQL", status=ServiceStatus.SUCCEEDED, duration_seconds=30.0
    )

    result = single_service_restore_job.execute_in_process(
        resources=dagster_resources,
        run_config=_single_restore_run_config("PostgreSQL"),
    )

    assert result.success
    mock_orchestrator.run_single_restore.assert_called_once_with(
        service_name="PostgreSQL", timestamp="2026-02-19_02-00-00"
    )


@patch("aihub_backup.dagster.ops.restore_ops.build_orchestrator")
def test_single_service_restore_fails(
    mock_build_orchestrator: MagicMock,
    dagster_resources: dict[str, object],
) -> None:
    """Single service restore job fails when the service restore fails."""
    mock_orchestrator = MagicMock()
    mock_s3 = MagicMock()
    mock_build_orchestrator.return_value = (mock_orchestrator, mock_s3)
    mock_orchestrator.run_single_restore.return_value = ServiceResult(
        name="Milvus", status=ServiceStatus.FAILED, duration_seconds=2.0, error="Connection refused"
    )

    result = single_service_restore_job.execute_in_process(
        resources=dagster_resources,
        run_config=_single_restore_run_config("Milvus"),
        raise_on_error=False,
    )

    assert not result.success
