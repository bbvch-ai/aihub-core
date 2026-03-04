from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import redis

from aihub_backup.services.valkey import ValkeyHandler
from aihub_backup.settings import BackupSettings


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    with patch("aihub_backup.services.valkey.tempfile.mkdtemp", return_value=str(tmp_path)):
        yield tmp_path


@pytest.fixture
def valkey_handler(settings: BackupSettings) -> ValkeyHandler:
    s3 = MagicMock()
    docker = MagicMock()
    docker.container_exists.return_value = True
    docker.get_container_image.return_value = "valkey/valkey:8.1"
    docker.get_volume_mount.return_value = "/var/lib/docker/volumes/valkey-data/_data"
    docker.start_and_wait.return_value = (0, "")
    return ValkeyHandler(settings, s3, docker)


@pytest.fixture
def mock_redis() -> MagicMock:
    return MagicMock()


def _create_fake_rdb(container: str, src: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(b"REDIS0011" + b"\x00" * 100)


def test_backup_triggers_bgsave_and_uploads(
    tmp_dir: Path, valkey_handler: ValkeyHandler, mock_redis: MagicMock
) -> None:
    docker = valkey_handler._docker
    docker.container_is_running.return_value = True
    docker.copy_from_container.side_effect = _create_fake_rdb

    mock_redis.lastsave.side_effect = [
        datetime(2026, 1, 1, 0, 0, 0),
        datetime(2026, 1, 1, 0, 0, 10),
    ]

    with patch.object(valkey_handler, "_create_client", return_value=mock_redis):
        valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    mock_redis.bgsave.assert_called_once()
    docker.copy_from_container.assert_called_once()
    valkey_handler._s3.upload_file.assert_called_once()

    s3_key = valkey_handler._s3.upload_file.call_args[0][1]
    assert s3_key == "2026-02-19_02-00-00/valkey.rdb"


def test_backup_raises_when_container_not_running(valkey_handler: ValkeyHandler) -> None:
    valkey_handler._docker.container_is_running.return_value = False

    with pytest.raises(RuntimeError, match="not running"):
        valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")


def test_backup_raises_on_bgsave_timeout(valkey_handler: ValkeyHandler, mock_redis: MagicMock) -> None:
    docker = valkey_handler._docker
    docker.container_is_running.return_value = True

    same_time = datetime(2026, 1, 1, 0, 0, 0)
    mock_redis.lastsave.return_value = same_time

    with (
        patch.object(valkey_handler, "_create_client", return_value=mock_redis),
        patch("aihub_backup.services.valkey.BGSAVE_TIMEOUT", 4),
        patch("aihub_backup.services.valkey.time.sleep"),
        pytest.raises(RuntimeError, match="did not complete"),
    ):
        valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")


def test_backup_handles_bgsave_already_in_progress(
    tmp_dir: Path, valkey_handler: ValkeyHandler, mock_redis: MagicMock
) -> None:
    docker = valkey_handler._docker
    docker.container_is_running.return_value = True
    docker.copy_from_container.side_effect = _create_fake_rdb

    mock_redis.lastsave.side_effect = [
        datetime(2026, 1, 1, 0, 0, 0),
        datetime(2026, 1, 1, 0, 0, 10),
    ]
    mock_redis.bgsave.side_effect = redis.exceptions.ResponseError("Background saving already in progress")

    with patch.object(valkey_handler, "_create_client", return_value=mock_redis):
        valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    valkey_handler._s3.upload_file.assert_called_once()


def test_restore_uses_temp_container_for_cleanup(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    """Restore creates a temp sibling container to clean data, then copies new data."""
    docker = valkey_handler._docker

    def fake_download(s3_key: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"REDIS0011" + b"\x00" * 100)

    valkey_handler._s3.download_file.side_effect = fake_download

    valkey_handler.restore("2026-02-19_02-00-00")

    valkey_handler._s3.download_file.assert_called_once()
    docker.stop_container.assert_called_once_with("valkey")

    # Temp container created with cleanup command and shared data volume
    docker.create_container.assert_called_once()
    create_kwargs = docker.create_container.call_args
    assert create_kwargs.kwargs["command"] == ["rm", "-rf", "/data/appendonlydir", "/data/dump.rdb"]
    assert "/var/lib/docker/volumes/valkey-data/_data" in create_kwargs.kwargs["volumes"]

    docker.start_and_wait.assert_called_once()
    docker.remove_container.assert_called_once()

    assert docker.copy_to_container.call_count == 2
    aof_copy_call = docker.copy_to_container.call_args_list[0]
    assert aof_copy_call[0][2] == "/data/appendonlydir"
    rdb_copy_call = docker.copy_to_container.call_args_list[1]
    assert rdb_copy_call[0][2] == "/data/dump.rdb"

    docker.start_container.assert_called_once_with("valkey")
    docker.wait_for_healthy.assert_called_once_with("valkey", timeout=60)


def test_restore_aof_directory_structure(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    """The AOF directory sent to copy_to_container has the expected file layout."""
    docker = valkey_handler._docker

    captured_files: list[str] = []
    captured_manifest: str = ""

    def capture_copy_to(container: str, src: Path, dst: str) -> None:
        if src.name == "appendonlydir":
            captured_files.extend(f.name for f in src.iterdir())
            manifest = src / "appendonly.aof.manifest"
            if manifest.exists():
                nonlocal captured_manifest
                captured_manifest = manifest.read_text()

    docker.copy_to_container.side_effect = capture_copy_to

    def fake_download(s3_key: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"REDIS0011" + b"\x00" * 100)

    valkey_handler._s3.download_file.side_effect = fake_download

    valkey_handler.restore("2026-02-19_02-00-00")

    assert "appendonly.aof.1.base.rdb" in captured_files
    assert "appendonly.aof.1.incr.aof" in captured_files
    assert "appendonly.aof.manifest" in captured_files
    assert "appendonly.aof.1.base.rdb" in captured_manifest


def test_restore_removes_temp_container_on_cleanup_failure(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    """Even when the cleanup container fails, it is removed."""
    docker = valkey_handler._docker
    docker.start_and_wait.return_value = (1, "rm: cannot remove '/data/appendonlydir': Permission denied")

    def fake_download(s3_key: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"REDIS0011" + b"\x00" * 100)

    valkey_handler._s3.download_file.side_effect = fake_download

    with pytest.raises(RuntimeError, match="data cleanup failed"):
        valkey_handler.restore("2026-02-19_02-00-00")

    docker.remove_container.assert_called_once()


def test_restore_works_when_container_already_stopped(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    """Restore succeeds even when the container is already stopped (full restore scenario)."""
    docker = valkey_handler._docker
    docker.stop_container.return_value = False  # Already stopped

    def fake_download(s3_key: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"REDIS0011" + b"\x00" * 100)

    valkey_handler._s3.download_file.side_effect = fake_download

    valkey_handler.restore("2026-02-19_02-00-00")

    # Temp container cleanup still runs
    docker.create_container.assert_called_once()
    docker.start_and_wait.assert_called_once()
    # Data is copied and container restarted
    assert docker.copy_to_container.call_count == 2
    docker.start_container.assert_called_once_with("valkey")


def test_restore_does_not_mutate_container_if_preparation_fails(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    """If AOF preparation fails, no container mutation occurs (stop, sidecar, copy)."""
    docker = valkey_handler._docker

    def fake_download(s3_key: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"REDIS0011" + b"\x00" * 100)

    valkey_handler._s3.download_file.side_effect = fake_download

    with (
        patch("aihub_backup.services.valkey.shutil.copy2", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        valkey_handler.restore("2026-02-19_02-00-00")

    docker.stop_container.assert_not_called()
    docker.create_container.assert_not_called()
    docker.copy_to_container.assert_not_called()
