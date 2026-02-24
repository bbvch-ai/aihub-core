from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.models import BackupMode, ServiceStatus
from aihub_backup.orchestrator import APP_CONTAINERS, Orchestrator
from aihub_backup.settings import BackupSettings


@pytest.fixture
def mock_handler() -> MagicMock:
    handler = MagicMock()
    handler.service_name = "TestService"
    return handler


@pytest.fixture
def orchestrator(settings: BackupSettings, mock_handler: MagicMock) -> Orchestrator:
    s3 = MagicMock()
    docker = MagicMock()
    return Orchestrator(settings, s3, docker, [mock_handler])


def test_run_backup_succeeds(orchestrator: Orchestrator, mock_handler: MagicMock) -> None:
    with patch("aihub_backup.retention.run_retention"):
        summary = orchestrator.run_backup(mode=BackupMode.ONLINE)

    assert summary.mode == BackupMode.ONLINE
    assert len(summary.results) == 1
    assert summary.results[0].status == ServiceStatus.SUCCEEDED
    mock_handler.backup.assert_called_once()


def test_run_backup_captures_failure(orchestrator: Orchestrator, mock_handler: MagicMock) -> None:
    mock_handler.backup.side_effect = RuntimeError("Database connection failed")

    with patch("aihub_backup.retention.run_retention"):
        summary = orchestrator.run_backup(mode=BackupMode.ONLINE)

    assert summary.results[0].status == ServiceStatus.FAILED
    assert "Database connection failed" in (summary.results[0].error or "")


def test_run_backup_offline_stops_and_restarts_apps(settings: BackupSettings) -> None:
    s3 = MagicMock()
    docker = MagicMock()
    docker.container_exists.return_value = True
    docker.stop_container.return_value = True
    docker.wait_for_healthy.return_value = True

    handler = MagicMock()
    handler.service_name = "TestService"

    orchestrator = Orchestrator(settings, s3, docker, [handler])

    with patch("aihub_backup.retention.run_retention"):
        orchestrator.run_backup(mode=BackupMode.OFFLINE)

    # Should have called stop_container for app containers
    assert docker.stop_container.called
    # Should have called start_container for restart
    assert docker.start_container.called


def test_list_backups(orchestrator: Orchestrator) -> None:
    orchestrator._s3.list_prefixes.return_value = [
        "2026-02-17_02-00-00_online",
        "2026-02-18_02-00-00_offline",
    ]
    orchestrator._s3.count_objects.return_value = 5

    entries = orchestrator.list_backups()
    assert len(entries) == 2
    assert entries[0].mode == "online"
    assert entries[1].mode == "offline"
    assert entries[0].file_count == 5


def test_list_backups_skips_non_backup_prefixes(orchestrator: Orchestrator) -> None:
    orchestrator._s3.list_prefixes.return_value = [
        "2026-02-17_02-00-00_online",
        "random-folder",
        "short",
    ]
    orchestrator._s3.count_objects.return_value = 5

    entries = orchestrator.list_backups()
    assert len(entries) == 1
    assert entries[0].prefix == "2026-02-17_02-00-00_online"


def _make_restore_orchestrator(settings: BackupSettings, handler_names: list[str] | None = None) -> Orchestrator:
    """Create an orchestrator with mocked handlers for restore tests."""
    s3 = MagicMock()
    docker = MagicMock()
    docker.container_exists.return_value = True
    docker.stop_container.return_value = True
    docker.wait_for_healthy.return_value = True

    names = handler_names or ["PostgreSQL", "Neo4j", "ClickHouse", "Valkey", "NATS", "Milvus"]
    handlers = []
    for name in names:
        h = MagicMock()
        h.service_name = name
        handlers.append(h)

    orchestrator = Orchestrator(settings, s3, docker, handlers)

    # Mock S3 validation
    s3.file_exists.return_value = True
    s3.list_prefixes.side_effect = lambda prefix="": (
        ["2026-02-19_02-00-00_online/milvus_backup_2026_02_19"] if prefix else ["2026-02-19_02-00-00_online"]
    )
    s3.find_latest_backup.return_value = "2026-02-19_02-00-00_online"
    s3.resolve_timestamp.return_value = "2026-02-19_02-00-00_online"

    return orchestrator


def test_run_restore_full_flow(settings: BackupSettings) -> None:
    """Full restore completes all phases."""
    orchestrator = _make_restore_orchestrator(settings)

    summary = orchestrator.run_restore(timestamp="2026-02-19_02-00-00_online", force=True)

    assert summary.mode == BackupMode.ONLINE
    assert len(summary.results) == 6
    assert all(r.status == ServiceStatus.SUCCEEDED for r in summary.results)


def test_run_restore_auto_selects_latest(settings: BackupSettings) -> None:
    """Restore auto-selects latest backup when no timestamp given."""
    orchestrator = _make_restore_orchestrator(settings)

    summary = orchestrator.run_restore(force=True)

    assert summary.timestamp == "2026-02-19_02-00-00_online"
    assert len(summary.results) == 6


def test_run_restore_aborts_on_failure_without_force(settings: BackupSettings) -> None:
    """Without force, restore aborts on first service failure and restarts all services."""
    orchestrator = _make_restore_orchestrator(settings)

    # Make PostgreSQL restore fail
    pg_handler = orchestrator._handlers["PostgreSQL"]
    pg_handler.restore.side_effect = RuntimeError("pg_restore failed")

    with pytest.raises(RuntimeError, match="pg_restore failed"):
        orchestrator.run_restore(timestamp="2026-02-19_02-00-00_online", force=False)

    # All services should be restarted after failure
    docker = orchestrator._docker
    assert docker.start_container.called


def test_run_restore_continues_with_force(settings: BackupSettings) -> None:
    """With force=True, restore continues past failures."""
    orchestrator = _make_restore_orchestrator(settings)

    # Make Neo4j restore fail
    neo4j_handler = orchestrator._handlers["Neo4j"]
    neo4j_handler.restore.side_effect = RuntimeError("neo4j load failed")

    summary = orchestrator.run_restore(timestamp="2026-02-19_02-00-00_online", force=True)

    # Should complete with Neo4j as FAILED, others as SUCCEEDED
    neo4j_result = next(r for r in summary.results if r.name == "Neo4j")
    assert neo4j_result.status == ServiceStatus.FAILED

    succeeded = [r for r in summary.results if r.status == ServiceStatus.SUCCEEDED]
    assert len(succeeded) == 5


def test_run_restore_validates_missing_backups(settings: BackupSettings) -> None:
    """Restore fails validation when any backup files are missing."""
    orchestrator = _make_restore_orchestrator(settings)
    orchestrator._s3.file_exists.return_value = False
    orchestrator._s3.list_prefixes.return_value = []

    with pytest.raises(RuntimeError, match="Missing backups"):
        orchestrator.run_restore(timestamp="2026-02-19_02-00-00_online")


def test_run_backup_captures_retention_warning(orchestrator: Orchestrator, mock_handler: MagicMock) -> None:
    """Retention failure is captured as a warning in the summary, not raised."""
    with patch("aihub_backup.orchestrator.run_retention", side_effect=RuntimeError("S3 timeout")):
        summary = orchestrator.run_backup(mode=BackupMode.ONLINE)

    assert summary.retention_warning == "S3 timeout"
    assert summary.results[0].status == ServiceStatus.SUCCEEDED


def test_run_backup_captures_unexpected_exception(orchestrator: Orchestrator, mock_handler: MagicMock) -> None:
    """Unexpected exception types (e.g. ValueError) are captured as FAILED results."""
    mock_handler.backup.side_effect = ValueError("unexpected error")

    with patch("aihub_backup.retention.run_retention"):
        summary = orchestrator.run_backup(mode=BackupMode.ONLINE)

    assert summary.results[0].status == ServiceStatus.FAILED
    assert "unexpected error" in (summary.results[0].error or "")


def test_single_restore_stops_apps_and_restarts_all(settings: BackupSettings) -> None:
    """Single restore stops app containers, restores the service, and restarts everything."""
    orchestrator = _make_restore_orchestrator(settings)
    docker = orchestrator._docker

    result = orchestrator.run_single_restore("PostgreSQL", timestamp="2026-02-19_02-00-00_online")

    assert result.status == ServiceStatus.SUCCEEDED
    orchestrator._handlers["PostgreSQL"].restore.assert_called_once()

    # App containers should be stopped
    stop_calls = [call[0][0] for call in docker.stop_container.call_args_list]
    for app in APP_CONTAINERS:
        assert app in stop_calls

    # All services should be restarted afterwards
    assert docker.start_container.called


def test_single_restore_restarts_services_on_failure(settings: BackupSettings) -> None:
    """Even when single restore fails, all services are restarted."""
    orchestrator = _make_restore_orchestrator(settings)

    pg_handler = orchestrator._handlers["PostgreSQL"]
    pg_handler.restore.side_effect = RuntimeError("pg_restore failed")

    with pytest.raises(RuntimeError, match="pg_restore failed"):
        orchestrator.run_single_restore("PostgreSQL", timestamp="2026-02-19_02-00-00_online")

    # Services should still be restarted (finally block)
    assert orchestrator._docker.start_container.called


def test_single_restore_rejects_unknown_service(settings: BackupSettings) -> None:
    """Single restore raises for unknown service names."""
    orchestrator = _make_restore_orchestrator(settings)

    with pytest.raises(RuntimeError, match="Unknown service"):
        orchestrator.run_single_restore("NonExistent", timestamp="2026-02-19_02-00-00_online")
