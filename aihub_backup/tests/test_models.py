from aihub_backup.models import BackupEntry, BackupMode, BackupSummary, ServiceResult, ServiceStatus


def test_backup_mode_values() -> None:
    assert BackupMode.ONLINE == "online"
    assert BackupMode.OFFLINE == "offline"


def test_service_status_values() -> None:
    assert ServiceStatus.SUCCEEDED == "succeeded"
    assert ServiceStatus.FAILED == "failed"
    assert ServiceStatus.SKIPPED == "skipped"


def test_service_result_defaults() -> None:
    result = ServiceResult(name="PostgreSQL", status=ServiceStatus.SUCCEEDED)
    assert result.duration_seconds == 0.0
    assert result.error is None


def test_backup_summary() -> None:
    summary = BackupSummary(
        timestamp="2026-02-18_14-00-00",
        mode=BackupMode.ONLINE,
        results=[
            ServiceResult(name="PostgreSQL", status=ServiceStatus.SUCCEEDED, duration_seconds=10.5),
            ServiceResult(name="Milvus", status=ServiceStatus.SKIPPED),
        ],
        total_duration_seconds=15.0,
    )
    assert len(summary.results) == 2
    assert summary.results[0].name == "PostgreSQL"
    assert summary.results[1].status == ServiceStatus.SKIPPED


# ---------------------------------------------------------------------------
# BackupEntry._parse_prefix
# ---------------------------------------------------------------------------


def test_parse_prefix_online() -> None:
    entry = BackupEntry(prefix="2026-02-19_02-00-00_online", file_count=5)
    assert entry.timestamp == "2026-02-19_02-00-00"
    assert entry.mode == BackupMode.ONLINE


def test_parse_prefix_offline() -> None:
    entry = BackupEntry(prefix="2026-02-19_02-00-00_offline", file_count=3)
    assert entry.timestamp == "2026-02-19_02-00-00"
    assert entry.mode == BackupMode.OFFLINE


def test_parse_prefix_bare() -> None:
    """A prefix without a mode suffix falls back to None."""
    entry = BackupEntry(prefix="2026-02-19_02-00-00", file_count=1)
    assert entry.timestamp == "2026-02-19_02-00-00"
    assert entry.mode is None


def test_parse_prefix_unrecognized_suffix() -> None:
    """An unrecognized suffix (e.g. '_manual') keeps the full prefix as timestamp."""
    entry = BackupEntry(prefix="2026-02-19_02-00-00_manual", file_count=2)
    assert entry.timestamp == "2026-02-19_02-00-00_manual"
    assert entry.mode is None
