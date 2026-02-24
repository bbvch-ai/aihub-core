import shutil
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.services.clickhouse import ClickHouseHandler, _validate_backup_name
from aihub_backup.settings import BackupSettings


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    with patch("aihub_backup.services.clickhouse.tempfile.mkdtemp", return_value=str(tmp_path)):
        yield tmp_path


@pytest.fixture
def ch_handler(settings: BackupSettings) -> ClickHouseHandler:
    s3 = MagicMock()
    docker = MagicMock()
    return ClickHouseHandler(settings, s3, docker)


def test_validate_backup_name_valid() -> None:
    assert _validate_backup_name("backup_2026_02_19_02_00_00") == "backup_2026_02_19_02_00_00"


def test_validate_backup_name_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid ClickHouse backup name"):
        _validate_backup_name("backup_drop;--")


def test_validate_backup_name_rejects_unicode() -> None:
    """Unicode word characters (e.g. accented letters) should be rejected."""
    with pytest.raises(ValueError, match="Invalid ClickHouse backup name"):
        _validate_backup_name("backup_café")


def test_backup_flow(tmp_dir: Path, ch_handler: ClickHouseHandler) -> None:
    """Backup: exec SELECT 1 → list tables → BACKUP → copy → compress → upload."""
    docker = ch_handler._docker
    docker.exec_in_container.side_effect = [
        (0, "1\n"),  # SELECT 1
        (0, "events\nlogs\n"),  # list tables
        (0, ""),  # BACKUP DATABASE
        (0, ""),  # rm -rf cleanup
    ]

    def fake_copy_from(container: str, src: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "metadata.sql").write_text("CREATE TABLE ...")

    docker.copy_from_container.side_effect = fake_copy_from

    ch_handler.backup("2026_02_19_02_00_00", "2026-02-19_02-00-00_online")

    assert docker.exec_in_container.call_count == 4
    ch_handler._s3.upload_file.assert_called_once()
    s3_key = ch_handler._s3.upload_file.call_args[0][1]
    assert s3_key == "2026-02-19_02-00-00_online/clickhouse.tar.gz"


def test_backup_skips_empty_database(tmp_dir: Path, ch_handler: ClickHouseHandler) -> None:
    """Backup is skipped when no user tables exist in default database."""
    docker = ch_handler._docker
    docker.exec_in_container.side_effect = [
        (0, "1\n"),  # SELECT 1
        (0, ""),  # empty table list
    ]

    ch_handler.backup("2026_02_19_02_00_00", "2026-02-19_02-00-00_online")

    ch_handler._s3.upload_file.assert_not_called()


def test_backup_passes_password_via_env(tmp_dir: Path, ch_handler: ClickHouseHandler) -> None:
    """Password is passed via environment dict, not in CLI args."""
    docker = ch_handler._docker
    docker.exec_in_container.side_effect = [
        (0, "1\n"),
        (0, ""),  # empty tables → skip
    ]

    ch_handler.backup("2026_02_19_02_00_00", "2026-02-19_02-00-00_online")

    # Check that environment was passed (not password in args)
    for call in docker.exec_in_container.call_args_list:
        kwargs = call.kwargs if call.kwargs else {}
        env = kwargs.get("environment", {})
        assert "CLICKHOUSE_PASSWORD" in env
        cmd = call.args[1] if len(call.args) > 1 else call.kwargs.get("command", [])
        assert not any("--password=" in str(arg) for arg in cmd)


def test_restore_flow(tmp_dir: Path, ch_handler: ClickHouseHandler) -> None:
    """Restore: download → extract → drop tables → copy to container → RESTORE → cleanup."""
    docker = ch_handler._docker
    docker.exec_in_container.side_effect = [
        (0, "events\nlogs\n"),  # list existing tables
        (0, ""),  # DROP TABLE events
        (0, ""),  # DROP TABLE logs
        (0, ""),  # RESTORE DATABASE
        (0, ""),  # rm -rf cleanup
    ]

    # Create a fake archive for download
    archive_dir = tmp_dir / "staging"
    archive_dir.mkdir(parents=True)
    backup_subdir = archive_dir / "clickhouse" / "backup_test"
    backup_subdir.mkdir(parents=True)
    (backup_subdir / "metadata.sql").write_text("CREATE TABLE ...")
    archive_path = archive_dir / "clickhouse.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(str(archive_dir / "clickhouse"), arcname="clickhouse")

    def fake_download(s3_key: str, local_path: Path) -> None:
        shutil.copy(archive_path, local_path)

    ch_handler._s3.download_file.side_effect = fake_download

    ch_handler.restore("2026-02-19_02-00-00_online")

    ch_handler._s3.download_file.assert_called_once()
    docker.copy_to_container.assert_called_once()
    # 1 list tables + 2 drops + 1 RESTORE + 1 rm cleanup = 5
    assert docker.exec_in_container.call_count == 5


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------


def test_backup_accepts_hyphenated_timestamp(tmp_dir: Path, ch_handler: ClickHouseHandler) -> None:
    """Timestamps contain hyphens (e.g. 2026-02-19_02-00-00_online).

    The backup_name must replace hyphens with underscores before validation,
    otherwise _validate_backup_name rejects it.
    Regression: backup_name was built without .replace('-', '_').
    """
    docker = ch_handler._docker
    docker.exec_in_container.side_effect = [
        (0, "1\n"),  # SELECT 1
        (0, "events\n"),  # list tables
        (0, ""),  # BACKUP DATABASE
        (0, ""),  # rm -rf cleanup
    ]

    def fake_copy_from(container: str, src: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "metadata.sql").write_text("CREATE TABLE ...")

    docker.copy_from_container.side_effect = fake_copy_from

    # This timestamp contains hyphens — must NOT raise ValueError
    ch_handler.backup("2026-02-19_02-00-00_online", "2026-02-19_02-00-00_online")


def test_restore_skips_invalid_table_name(tmp_dir: Path, ch_handler: ClickHouseHandler, caplog: pytest.LogCaptureFixture) -> None:
    """Tables with invalid names returned by system.tables are skipped with a warning."""
    import shutil
    import tarfile

    docker = ch_handler._docker
    docker.exec_in_container.side_effect = [
        (0, "valid_table\n'; DROP DATABASE --\n"),  # list existing tables
        (0, ""),  # DROP TABLE valid_table
        (0, ""),  # RESTORE DATABASE
        (0, ""),  # rm -rf cleanup
    ]

    archive_dir = tmp_dir / "staging"
    archive_dir.mkdir(parents=True)
    backup_subdir = archive_dir / "clickhouse" / "backup_test"
    backup_subdir.mkdir(parents=True)
    (backup_subdir / "metadata.sql").write_text("CREATE TABLE ...")
    archive_path = archive_dir / "clickhouse.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(str(archive_dir / "clickhouse"), arcname="clickhouse")

    def fake_download(s3_key: str, local_path: Path) -> None:
        shutil.copy(archive_path, local_path)

    ch_handler._s3.download_file.side_effect = fake_download

    ch_handler.restore("2026-02-19_02-00-00_online")

    assert any("Skipping table with invalid name" in r.message for r in caplog.records)
    # Only 1 DROP (valid_table), the invalid name is skipped
    drop_calls = [
        c for c in docker.exec_in_container.call_args_list if any("DROP TABLE" in str(a) for a in c[0])
    ]
    assert len(drop_calls) == 1


def test_backup_raises_on_table_listing_failure(tmp_dir: Path, ch_handler: ClickHouseHandler) -> None:
    """When the table listing query fails (non-zero exit), raise immediately.

    Regression: exit_code was not checked after the system.tables query,
    so error output was silently treated as table names.
    """
    docker = ch_handler._docker
    docker.exec_in_container.side_effect = [
        (0, "1\n"),  # SELECT 1 — reachable
        (1, "Code: 516. Authentication failed"),  # table listing fails
    ]

    with pytest.raises(RuntimeError, match="table listing"):
        ch_handler.backup("2026_02_19_02_00_00", "2026-02-19_02-00-00_online")
