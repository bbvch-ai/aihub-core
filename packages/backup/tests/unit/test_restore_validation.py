from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.backup.dagster.assets.restore_session_factory import _validate_backup_completeness_or_raise


def _mock_s3_all_present() -> MagicMock:
    s3 = MagicMock()
    s3.file_exists.return_value = True
    s3.list_prefixes.side_effect = lambda prefix: (
        ["clickhouse_backup_1"] if "clickhouse" in prefix else ["milvus_backup_20260101"]
    )
    return s3


def _mock_s3_all_missing() -> MagicMock:
    s3 = MagicMock()
    s3.file_exists.return_value = False
    s3.list_prefixes.return_value = []
    return s3


def test_validate_passes_when_all_backups_present() -> None:
    s3 = _mock_s3_all_present()
    context = MagicMock()
    _validate_backup_completeness_or_raise(s3, "2026-01-01_10-00-00", context)
    context.log.info.assert_called_with("All backups validated")


def test_validate_raises_when_all_backups_missing() -> None:
    s3 = _mock_s3_all_missing()
    context = MagicMock()
    with pytest.raises(RuntimeError, match="Missing backups"):
        _validate_backup_completeness_or_raise(s3, "2026-01-01_10-00-00", context)


def test_validate_reports_specific_missing_services() -> None:
    s3 = MagicMock()
    s3.file_exists.side_effect = lambda key: "postgres-main" in key
    s3.list_prefixes.return_value = []
    context = MagicMock()

    with pytest.raises(RuntimeError, match="PostgreSQL \\(FerretDB\\)") as exc_info:
        _validate_backup_completeness_or_raise(s3, "2026-01-01_10-00-00", context)

    error_msg = str(exc_info.value)
    assert "PostgreSQL (FerretDB)" in error_msg
    assert "Neo4j" in error_msg
    assert "ClickHouse" in error_msg
    assert "Valkey" in error_msg
    assert "NATS JetStream" in error_msg
    assert "Milvus" in error_msg
    assert "PostgreSQL (main)" not in error_msg
