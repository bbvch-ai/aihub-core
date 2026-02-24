import io
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.services.postgres import PostgresHandler
from aihub_backup.settings import BackupSettings


@pytest.fixture
def postgres_handler(settings: BackupSettings) -> PostgresHandler:
    s3 = MagicMock()
    return PostgresHandler(settings, s3)


def _make_popen_mock(*, returncode: int = 0, stdout_data: bytes = b"SQL DUMP") -> MagicMock:
    """Build a Popen mock with BytesIO stdout/stdin/stderr to avoid infinite reads.

    Supports context manager protocol (with Popen(...) as proc).
    """
    proc = MagicMock()
    proc.stdout = io.BytesIO(stdout_data)
    proc.stdin = io.BytesIO()
    proc.stderr = io.BytesIO(b"")
    proc.returncode = returncode
    proc.wait.return_value = returncode
    proc.__enter__ = MagicMock(return_value=proc)
    proc.__exit__ = MagicMock(return_value=False)
    return proc


@patch("aihub_backup.services.postgres.subprocess.Popen")
def test_backup_dumps_both_hosts(mock_popen: MagicMock, postgres_handler: PostgresHandler) -> None:
    """Backup calls pg_dumpall for both main and FerretDB hosts."""
    mock_popen.side_effect = lambda *a, **kw: _make_popen_mock()

    postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    assert mock_popen.call_count == 2
    assert postgres_handler._s3.upload_file.call_count == 2

    s3_keys = [call[0][1] for call in postgres_handler._s3.upload_file.call_args_list]
    assert "2026-02-19_02-00-00_online/postgres-main.sql.gz" in s3_keys
    assert "2026-02-19_02-00-00_online/postgres-ferretdb.sql.gz" in s3_keys


@patch("aihub_backup.services.postgres.subprocess.Popen")
def test_backup_raises_on_pg_dumpall_failure(mock_popen: MagicMock, postgres_handler: PostgresHandler) -> None:
    """Backup raises CalledProcessError when pg_dumpall fails."""
    mock_popen.side_effect = lambda *a, **kw: _make_popen_mock(returncode=1, stdout_data=b"")

    with pytest.raises(subprocess.CalledProcessError):
        postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")


@patch("aihub_backup.services.postgres.subprocess.Popen")
def test_backup_passes_password_via_env(mock_popen: MagicMock, postgres_handler: PostgresHandler) -> None:
    """pg_dumpall receives password via PGPASSWORD env var, not CLI args."""
    mock_popen.side_effect = lambda *a, **kw: _make_popen_mock(stdout_data=b"SQL")

    postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    call_kwargs = mock_popen.call_args_list[0]
    env = call_kwargs.kwargs.get("env") or call_kwargs[1].get("env", {})
    assert "PGPASSWORD" in env
    cmd = call_kwargs[0][0] if call_kwargs[0] else call_kwargs.kwargs.get("args", [])
    assert not any("testpass" in str(arg) for arg in cmd)


def _fake_download(s3_key: str, local_path: Path) -> None:
    """Write a small gzip file to simulate S3 download."""
    import gzip

    local_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(local_path, "wb") as f:
        f.write(b"-- SQL dump")


@patch("aihub_backup.services.postgres.subprocess.Popen")
def test_restore_downloads_and_runs_psql(mock_popen: MagicMock, postgres_handler: PostgresHandler) -> None:
    """Restore downloads dumps and runs psql for both hosts."""
    mock_popen.side_effect = lambda *a, **kw: _make_popen_mock()
    postgres_handler._s3.download_file.side_effect = _fake_download

    postgres_handler.restore("2026-02-19_02-00-00_online")

    assert mock_popen.call_count == 2


@patch("aihub_backup.services.postgres.subprocess.Popen")
def test_restore_passes_password_via_env(mock_popen: MagicMock, postgres_handler: PostgresHandler) -> None:
    """psql receives password via PGPASSWORD env var, not CLI args."""
    mock_popen.side_effect = lambda *a, **kw: _make_popen_mock()
    postgres_handler._s3.download_file.side_effect = _fake_download

    postgres_handler.restore("2026-02-19_02-00-00_online")

    call_kwargs = mock_popen.call_args_list[0]
    env = call_kwargs.kwargs.get("env") or call_kwargs[1].get("env", {})
    assert "PGPASSWORD" in env
