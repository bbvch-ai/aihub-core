from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aihub_backup.services.neo4j import Neo4jHandler
from aihub_backup.settings import BackupSettings


@pytest.fixture
def neo4j_handler(settings: BackupSettings) -> Neo4jHandler:
    s3 = MagicMock()
    docker = MagicMock()
    docker.container_exists.return_value = True
    docker.get_container_image.return_value = "neo4j:5.26"
    docker.get_volume_mount.return_value = "/var/lib/docker/volumes/neo4j-data/_data"
    return Neo4jHandler(settings, s3, docker)


def test_service_name(neo4j_handler: Neo4jHandler) -> None:
    assert neo4j_handler.service_name == "Neo4j"


def test_backup_lifecycle(neo4j_handler: Neo4jHandler) -> None:
    """Backup: stop → temp container dump → start → copy → upload."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "Dump completed")

    def fake_copy_from(container: str, src: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"NEO4J DUMP DATA")

    docker.copy_from_container.side_effect = fake_copy_from

    neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    docker.stop_container.assert_called_once_with("neo4j")
    docker.create_container.assert_called_once()
    docker.start_and_wait.assert_called_once()
    docker.start_container.assert_called_once_with("neo4j")
    docker.wait_for_healthy.assert_called_once_with("neo4j", timeout=120)
    neo4j_handler._s3.upload_file.assert_called_once()


def test_backup_restarts_neo4j_on_failure(neo4j_handler: Neo4jHandler) -> None:
    """Neo4j is restarted even when the dump fails."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (1, "Error: dump failed")

    with pytest.raises(RuntimeError, match="neo4j-admin dump failed"):
        neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    # Neo4j should still be started (once in normal flow since exit_code != 0
    # causes RuntimeError after start, then except block also starts)
    assert docker.start_container.called
    assert docker.wait_for_healthy.called


def test_backup_wait_for_healthy_called(neo4j_handler: Neo4jHandler) -> None:
    """wait_for_healthy is called after starting Neo4j."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "OK")

    def fake_copy_from(container: str, src: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"NEO4J DUMP")

    docker.copy_from_container.side_effect = fake_copy_from

    neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    docker.wait_for_healthy.assert_called_with("neo4j", timeout=120)


def test_restore_flow(neo4j_handler: Neo4jHandler) -> None:
    """Restore: download → stop → load → start → wait for healthy."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "Load completed")

    neo4j_handler.restore("2026-02-19_02-00-00_online")

    neo4j_handler._s3.download_file.assert_called_once()
    docker.stop_container.assert_called_once_with("neo4j")
    docker.create_container.assert_called_once()
    docker.copy_to_container.assert_called_once()
    docker.start_and_wait.assert_called_once()
    docker.start_container.assert_called_once_with("neo4j")
    docker.wait_for_healthy.assert_called_with("neo4j", timeout=120)


def test_restore_restarts_on_failure(neo4j_handler: Neo4jHandler) -> None:
    """Neo4j is restarted even when the load fails."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (1, "Error: load failed")

    with pytest.raises(RuntimeError, match="neo4j-admin load failed"):
        neo4j_handler.restore("2026-02-19_02-00-00_online")

    assert docker.start_container.called
    assert docker.wait_for_healthy.called


def test_backup_no_double_restart_after_upload_failure(neo4j_handler: Neo4jHandler) -> None:
    """When upload_file fails after Neo4j is already restarted, don't restart again."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "OK")

    def fake_copy_from(container: str, src: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"NEO4J DUMP")

    docker.copy_from_container.side_effect = fake_copy_from
    neo4j_handler._s3.upload_file.side_effect = RuntimeError("S3 upload failed")

    with pytest.raises(RuntimeError, match="S3 upload failed"):
        neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    # Neo4j should be restarted exactly once (in the try block), not again in except
    docker.wait_for_healthy.assert_called_once_with("neo4j", timeout=120)


def test_restore_no_double_restart_after_healthy(neo4j_handler: Neo4jHandler) -> None:
    """When restore succeeds through start+wait, except block skips redundant restart."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "OK")

    neo4j_handler.restore("2026-02-19_02-00-00_online")

    # start_container and wait_for_healthy should be called once (happy path only)
    docker.start_container.assert_called_once_with("neo4j")
    docker.wait_for_healthy.assert_called_once_with("neo4j", timeout=120)
