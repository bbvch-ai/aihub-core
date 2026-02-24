import shutil
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.services.nats import NatsHandler
from aihub_backup.settings import BackupSettings


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    with patch("aihub_backup.services.nats.tempfile.mkdtemp", return_value=str(tmp_path)):
        yield tmp_path


@pytest.fixture
def nats_handler(settings: BackupSettings) -> NatsHandler:
    s3 = MagicMock()
    return NatsHandler(settings, s3)


def test_service_name(nats_handler: NatsHandler) -> None:
    assert nats_handler.service_name == "NATS"


def test_nats_base_args_excludes_credentials(nats_handler: NatsHandler) -> None:
    args = nats_handler._nats_base_args()
    assert args[0] == "nats"
    assert "-s" in args
    assert "nats://localhost:4222" in args
    assert "--password" not in args


def test_nats_env_includes_credentials(nats_handler: NatsHandler) -> None:
    env = nats_handler._nats_env()
    assert env["NATS_TOKEN"] == "testpass"
    assert "PATH" in env


def test_list_streams_returns_empty_for_no_jetstream(nats_handler: NatsHandler) -> None:
    """Non-zero exit with 'no jetstream' in stderr returns empty list."""
    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="no jetstream", returncode=1)
        assert nats_handler._list_streams() == []


def test_list_streams_raises_on_connection_error(nats_handler: NatsHandler) -> None:
    """Non-zero exit with an actual error raises RuntimeError."""
    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="nats: error: connect failed", returncode=1)
        with pytest.raises(RuntimeError, match="nats stream list failed"):
            nats_handler._list_streams()


def test_backup_uploads_empty_archive_when_no_streams(nats_handler: NatsHandler) -> None:
    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        nats_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    nats_handler._s3.upload_file.assert_called_once()


def test_backup_backs_up_all_streams(tmp_dir: Path, nats_handler: NatsHandler) -> None:
    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        list_result = MagicMock(stdout="EVENTS\nCOMMANDS\n", returncode=0)
        backup_result = MagicMock(stdout="", returncode=0)
        mock_run.side_effect = [list_result, backup_result, backup_result]

        nats_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    # 1 list + 2 backups
    assert mock_run.call_count == 3
    nats_handler._s3.upload_file.assert_called_once()

    s3_key = nats_handler._s3.upload_file.call_args[0][1]
    assert s3_key == "2026-02-19_02-00-00_online/nats-jetstream.tar.gz"


def test_backup_fails_on_stream_backup_error(nats_handler: NatsHandler) -> None:
    with (
        patch("aihub_backup.services.nats.subprocess.run") as mock_run,
        pytest.raises(Exception),
    ):
        list_result = MagicMock(stdout="EVENTS\n", returncode=0)
        mock_run.side_effect = [list_result, Exception("backup failed")]

        nats_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")


def test_restore_restores_all_streams(tmp_dir: Path, nats_handler: NatsHandler) -> None:
    # Create a real tar.gz archive with stream directory structure in a staging dir
    staging = tmp_dir / "staging"
    staging.mkdir(parents=True)
    backup_dir = staging / "nats-backup"
    (backup_dir / "EVENTS").mkdir(parents=True)
    (backup_dir / "COMMANDS").mkdir(parents=True)
    source_tar = staging / "source.tar.gz"
    with tarfile.open(source_tar, "w:gz") as tar:
        tar.add(str(backup_dir), arcname="nats-backup")

    def fake_download(s3_key: str, dst: Path) -> None:
        shutil.copy(source_tar, dst)

    nats_handler._s3.download_file.side_effect = fake_download

    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        nats_handler.restore("2026-02-19_02-00-00_online")

    nats_handler._s3.download_file.assert_called_once()
    # 1 list_streams (check existing) + 2 stream restores (COMMANDS and EVENTS, sorted)
    assert mock_run.call_count == 3
