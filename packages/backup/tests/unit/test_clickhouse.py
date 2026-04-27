from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.backup.services.clickhouse import ClickHouseHandler
from swiss_ai_hub.backup.settings import BackupSettings


@pytest.fixture
def ch_handler(settings: BackupSettings) -> ClickHouseHandler:
    s3 = MagicMock()
    return ClickHouseHandler(settings, s3)


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


def test_validate_backup_name_valid() -> None:
    assert (
        ClickHouseHandler._validated_backup_name_or_raise("backup_2026_02_19_02_00_00") == "backup_2026_02_19_02_00_00"
    )


def test_validate_backup_name_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid ClickHouse backup name"):
        ClickHouseHandler._validated_backup_name_or_raise("backup_drop;--")


def test_validate_backup_name_rejects_unicode() -> None:
    with pytest.raises(ValueError, match="Invalid ClickHouse backup name"):
        ClickHouseHandler._validated_backup_name_or_raise("backup_café")


def test_backup_to_s3(ch_handler: ClickHouseHandler, mock_client: MagicMock) -> None:
    query_result = MagicMock()
    query_result.result_rows = [("events",), ("logs",)]
    mock_client.query.return_value = query_result

    with patch.object(ch_handler, "_create_client", return_value=mock_client):
        ch_handler.backup("2026_02_19_02_00_00", "2026-02-19_02-00-00")

    mock_client.command.assert_any_call("SELECT 1")
    mock_client.command.assert_any_call(
        "BACKUP DATABASE default TO Disk('backup_s3', '2026-02-19_02-00-00/clickhouse/backup_2026_02_19_02_00_00/')"
    )


def test_backup_empty_database_runs_backup_command(ch_handler: ClickHouseHandler, mock_client: MagicMock) -> None:
    with patch.object(ch_handler, "_create_client", return_value=mock_client):
        ch_handler.backup("2026_02_19_02_00_00", "2026-02-19_02-00-00")

    mock_client.command.assert_any_call("SELECT 1")
    mock_client.command.assert_any_call(
        "BACKUP DATABASE default TO Disk('backup_s3', '2026-02-19_02-00-00/clickhouse/backup_2026_02_19_02_00_00/')"
    )


def test_backup_accepts_hyphenated_timestamp(ch_handler: ClickHouseHandler, mock_client: MagicMock) -> None:
    query_result = MagicMock()
    query_result.result_rows = [("events",)]
    mock_client.query.return_value = query_result

    with patch.object(ch_handler, "_create_client", return_value=mock_client):
        ch_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    mock_client.command.assert_any_call(
        "BACKUP DATABASE default TO Disk('backup_s3', '2026-02-19_02-00-00/clickhouse/backup_2026_02_19_02_00_00/')"
    )


def test_restore_from_s3(ch_handler: ClickHouseHandler, mock_client: MagicMock) -> None:
    tables_result = MagicMock()
    tables_result.result_rows = [("events",), ("logs",)]
    mock_client.query.return_value = tables_result

    ch_handler._s3.list_prefixes.return_value = ["2026-02-19_02-00-00/clickhouse/backup_2026_02_19_02_00_00"]

    with patch.object(ch_handler, "_create_client", return_value=mock_client):
        ch_handler.restore("2026-02-19_02-00-00")

    drop_calls = [str(c) for c in mock_client.command.call_args_list if "DROP TABLE" in str(c)]
    assert len(drop_calls) == 2
    assert any("events" in c for c in drop_calls)
    assert any("logs" in c for c in drop_calls)

    mock_client.command.assert_any_call(
        "RESTORE DATABASE default FROM Disk('backup_s3', '2026-02-19_02-00-00/clickhouse/backup_2026_02_19_02_00_00/')"
    )


def test_restore_skips_when_no_backup_data(ch_handler: ClickHouseHandler, mock_client: MagicMock) -> None:
    ch_handler._s3.list_prefixes.return_value = []

    with patch.object(ch_handler, "_create_client", return_value=mock_client):
        ch_handler.restore("2026-02-19_02-00-00")

    mock_client.command.assert_not_called()


def test_restore_skips_invalid_table_name(
    ch_handler: ClickHouseHandler, mock_client: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    query_result = MagicMock()
    query_result.result_rows = [("valid_table",), ("'; DROP DATABASE --",)]
    mock_client.query.return_value = query_result

    ch_handler._s3.list_prefixes.return_value = ["2026-02-19_02-00-00/clickhouse/backup_2026_02_19_02_00_00"]

    with patch.object(ch_handler, "_create_client", return_value=mock_client):
        ch_handler.restore("2026-02-19_02-00-00")

    assert any("Skipping table with invalid name" in r.message for r in caplog.records)
    drop_calls = [c for c in mock_client.command.call_args_list if "DROP TABLE" in str(c)]
    assert len(drop_calls) == 1
    assert "valid_table" in str(drop_calls[0])


def test_backup_raises_on_unreachable(ch_handler: ClickHouseHandler, mock_client: MagicMock) -> None:
    mock_client.command.side_effect = Exception("Connection refused")

    with (
        patch.object(ch_handler, "_create_client", return_value=mock_client),
        pytest.raises(Exception, match="Connection refused"),
    ):
        ch_handler.backup("2026_02_19_02_00_00", "2026-02-19_02-00-00")


def test_has_backup_data_returns_false_for_empty_prefixes(ch_handler: ClickHouseHandler) -> None:
    ch_handler._s3.list_prefixes.return_value = []
    assert not ch_handler._has_backup_data("2026-02-19_02-00-00")

    ch_handler._s3.list_prefixes.return_value = ["2026-02-19_02-00-00/clickhouse/some_other_dir"]
    assert not ch_handler._has_backup_data("2026-02-19_02-00-00")


def test_has_backup_data_returns_true_when_backup_exists(ch_handler: ClickHouseHandler) -> None:
    ch_handler._s3.list_prefixes.return_value = ["2026-02-19_02-00-00/clickhouse/backup_2026_02_19_02_00_00"]
    assert ch_handler._has_backup_data("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.clickhouse.clickhouse_connect.get_client")
def test_create_client_sets_timeout(mock_get_client: MagicMock, ch_handler: ClickHouseHandler) -> None:
    ch_handler._create_client()

    mock_get_client.assert_called_once_with(
        host=ch_handler._settings.CLICKHOUSE_HOST,
        port=ch_handler._settings.CLICKHOUSE_PORT,
        username=ch_handler._settings.CLICKHOUSE_USER,
        password=ch_handler._settings.LANGFUSE_CLICKHOUSE_PASSWORD.get_secret_value(),
        send_receive_timeout=3600,
    )
