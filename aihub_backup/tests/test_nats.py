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


def test_wait_for_ready_succeeds_on_first_ping(nats_handler: NatsHandler) -> None:
    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        nats_handler._wait_for_ready()

    assert mock_run.call_count == 1
    assert "rtt" in mock_run.call_args[0][0]


def test_wait_for_ready_retries_until_success(nats_handler: NatsHandler) -> None:
    """Retries when NATS is not yet accepting connections."""
    with (
        patch("aihub_backup.services.nats.subprocess.run") as mock_run,
        patch("aihub_backup.services.nats.time.sleep"),
    ):
        fail = MagicMock(stdout="", stderr="no servers available", returncode=1)
        ok = MagicMock(stdout="", returncode=0)
        mock_run.side_effect = [fail, fail, ok]
        nats_handler._wait_for_ready()

    assert mock_run.call_count == 3


def test_wait_for_ready_raises_on_timeout(nats_handler: NatsHandler) -> None:
    with (
        patch("aihub_backup.services.nats.subprocess.run") as mock_run,
        patch("aihub_backup.services.nats.time.sleep"),
        patch("aihub_backup.services.nats.time.monotonic", side_effect=[0, 0, 100]),
        pytest.raises(RuntimeError, match="NATS not ready"),
    ):
        mock_run.return_value = MagicMock(stdout="", stderr="no servers", returncode=1)
        nats_handler._wait_for_ready()


def test_backup_uploads_empty_archive_when_no_streams(tmp_dir: Path, nats_handler: NatsHandler) -> None:
    captured_names: list[str] = []

    def capture_upload(path: Path, key: str) -> None:
        with tarfile.open(path, "r:gz") as tar:
            captured_names.extend(tar.getnames())

    nats_handler._s3.upload_file.side_effect = capture_upload

    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        ping_result = MagicMock(stdout="", returncode=0)
        list_result = MagicMock(stdout="", returncode=0)
        mock_run.side_effect = [ping_result, list_result]
        nats_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    nats_handler._s3.upload_file.assert_called_once()
    assert "nats-backup" in captured_names


def test_backup_backs_up_all_streams(tmp_dir: Path, nats_handler: NatsHandler) -> None:
    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        ping_result = MagicMock(stdout="", returncode=0)
        list_result = MagicMock(stdout="EVENTS\nCOMMANDS\n", returncode=0)
        backup_result = MagicMock(stdout="", returncode=0)
        mock_run.side_effect = [ping_result, list_result, backup_result, backup_result]

        nats_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    # 1 ping + 1 list + 2 backups
    assert mock_run.call_count == 4
    nats_handler._s3.upload_file.assert_called_once()

    s3_key = nats_handler._s3.upload_file.call_args[0][1]
    assert s3_key == "2026-02-19_02-00-00/nats-jetstream.tar.gz"


def test_backup_fails_on_stream_backup_error(nats_handler: NatsHandler) -> None:
    with (
        patch("aihub_backup.services.nats.subprocess.run") as mock_run,
        pytest.raises(RuntimeError, match="backup failed"),
    ):
        ping_result = MagicMock(stdout="", returncode=0)
        list_result = MagicMock(stdout="EVENTS\n", returncode=0)
        backup_result = MagicMock(stdout="", stderr="backup failed", returncode=1)
        mock_run.side_effect = [ping_result, list_result, backup_result]

        nats_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")


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
        # ping + list_streams returns existing stream "EVENTS", then rm + 2 restores succeed
        ping_result = MagicMock(stdout="", returncode=0)
        list_result = MagicMock(stdout="EVENTS\n", returncode=0)
        ok_result = MagicMock(stdout="", returncode=0)
        mock_run.side_effect = [ping_result, list_result, ok_result, ok_result, ok_result]
        nats_handler.restore("2026-02-19_02-00-00")

    nats_handler._s3.download_file.assert_called_once()
    # 1 ping + 1 list_streams + 1 stream rm (EVENTS) + 2 stream restores (COMMANDS, EVENTS)
    assert mock_run.call_count == 5

    # Verify the existing "EVENTS" stream was deleted before restore
    rm_call = mock_run.call_args_list[2]
    rm_args = rm_call[0][0]
    assert "rm" in rm_args
    assert "EVENTS" in rm_args


def test_restore_deletes_streams_not_in_backup(tmp_dir: Path, nats_handler: NatsHandler) -> None:
    """Streams created after backup are deleted during restore."""
    staging = tmp_dir / "staging"
    staging.mkdir(parents=True)
    backup_dir = staging / "nats-backup"
    (backup_dir / "A").mkdir(parents=True)
    source_tar = staging / "source.tar.gz"
    with tarfile.open(source_tar, "w:gz") as tar:
        tar.add(str(backup_dir), arcname="nats-backup")

    def fake_download(s3_key: str, dst: Path) -> None:
        shutil.copy(source_tar, dst)

    nats_handler._s3.download_file.side_effect = fake_download

    with patch("aihub_backup.services.nats.subprocess.run") as mock_run:
        # existing streams: A and B (B is not in backup)
        ping_result = MagicMock(stdout="", returncode=0)
        list_result = MagicMock(stdout="A\nB\n", returncode=0)
        ok_result = MagicMock(stdout="", returncode=0)
        # 1 ping + 1 list + 2 rm (A, B) + 1 restore (A)
        mock_run.side_effect = [ping_result, list_result, ok_result, ok_result, ok_result]
        nats_handler.restore("2026-02-19_02-00-00")

    rm_calls = [c for c in mock_run.call_args_list if "rm" in c[0][0]]
    rm_stream_names = [c[0][0][c[0][0].index("rm") + 1] for c in rm_calls]
    assert "A" in rm_stream_names
    assert "B" in rm_stream_names
