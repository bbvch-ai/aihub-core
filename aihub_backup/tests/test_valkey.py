from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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
    handler = ValkeyHandler(settings, s3, docker)
    return handler


def _create_fake_rdb(container: str, src: str, dst: Path) -> None:
    """Side effect for copy_from_container that creates a fake RDB file."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(b"REDIS0011" + b"\x00" * 100)


def test_backup_triggers_bgsave_and_uploads(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    docker = valkey_handler._docker
    docker.container_is_running.return_value = True
    docker.exec_in_container.side_effect = [
        (0, "(integer) 1708300000\n"),
        (0, "Background saving started\n"),
        (0, "(integer) 1708300010\n"),
    ]
    docker.copy_from_container.side_effect = _create_fake_rdb

    valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    docker.exec_in_container.assert_any_call(
        "valkey",
        ["valkey-cli", "--no-auth-warning", "BGSAVE"],
        environment={"REDISCLI_AUTH": "testpass"},
    )
    docker.copy_from_container.assert_called_once()
    valkey_handler._s3.upload_file.assert_called_once()

    s3_key = valkey_handler._s3.upload_file.call_args[0][1]
    assert s3_key == "2026-02-19_02-00-00_online/valkey.rdb"


def test_backup_raises_when_container_not_running(valkey_handler: ValkeyHandler) -> None:
    valkey_handler._docker.container_is_running.return_value = False

    with pytest.raises(RuntimeError, match="not running"):
        valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")


def test_backup_raises_on_bgsave_timeout(valkey_handler: ValkeyHandler) -> None:
    docker = valkey_handler._docker
    docker.container_is_running.return_value = True
    docker.exec_in_container.return_value = (0, "(integer) 1708300000\n")

    with (
        patch("aihub_backup.services.valkey.BGSAVE_TIMEOUT", 4),
        patch("aihub_backup.services.valkey.time.sleep"),
        pytest.raises(RuntimeError, match="did not complete"),
    ):
        valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")


def test_backup_handles_bgsave_already_in_progress(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    docker = valkey_handler._docker
    docker.container_is_running.return_value = True
    docker.exec_in_container.side_effect = [
        (0, "(integer) 1708300000\n"),
        (0, "Background saving already in progress\n"),
        (0, "(integer) 1708300010\n"),
    ]
    docker.copy_from_container.side_effect = _create_fake_rdb

    valkey_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    valkey_handler._s3.upload_file.assert_called_once()


def test_restore_stops_and_restarts_container(tmp_dir: Path, valkey_handler: ValkeyHandler) -> None:
    docker = valkey_handler._docker
    docker.container_is_running.return_value = True

    def fake_download(s3_key: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"REDIS0011" + b"\x00" * 100)

    valkey_handler._s3.download_file.side_effect = fake_download

    valkey_handler.restore("2026-02-19_02-00-00_online")

    valkey_handler._s3.download_file.assert_called_once()
    assert docker.exec_in_container.call_count == 2
    docker.exec_in_container.assert_any_call("valkey", ["rm", "-rf", "/data/appendonlydir"])
    docker.exec_in_container.assert_any_call("valkey", ["rm", "-rf", "/data/dump.rdb"])
    docker.stop_container.assert_called_once_with("valkey")
    # copy_to_container called twice: AOF dir + RDB file
    assert docker.copy_to_container.call_count == 2
    docker.start_container.assert_called_once_with("valkey")
    docker.wait_for_healthy.assert_called_once_with("valkey", timeout=60)
