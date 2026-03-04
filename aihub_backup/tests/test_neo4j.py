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


def test_backup_creates_dump_and_uploads(neo4j_handler: Neo4jHandler) -> None:
    """Backup: temp container dump → copy → upload (no container lifecycle)."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "Dump completed")

    def fake_copy_from(container: str, src: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"NEO4J DUMP DATA")

    docker.copy_from_container.side_effect = fake_copy_from

    neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    docker.create_container.assert_called_once()
    docker.start_and_wait.assert_called_once()
    neo4j_handler._s3.upload_file.assert_called_once()
    docker.stop_container.assert_not_called()
    docker.start_container.assert_not_called()


def test_backup_raises_on_dump_failure(neo4j_handler: Neo4jHandler) -> None:
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (1, "Error: dump failed")

    with pytest.raises(RuntimeError, match="neo4j-admin dump failed"):
        neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")


def test_backup_cleans_up_temp_container(neo4j_handler: Neo4jHandler) -> None:
    """Temp dump container is removed even on failure."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (1, "Error: dump failed")

    with pytest.raises(RuntimeError):
        neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    docker.remove_container.assert_called_once()


def test_restore_downloads_and_loads(neo4j_handler: Neo4jHandler) -> None:
    """Restore: download → load via temp container (no container lifecycle)."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "Load completed")

    neo4j_handler.restore("2026-02-19_02-00-00")

    neo4j_handler._s3.download_file.assert_called_once()
    docker.create_container.assert_called_once()
    docker.copy_to_container.assert_called_once()
    docker.start_and_wait.assert_called_once()
    docker.stop_container.assert_not_called()
    docker.start_container.assert_not_called()


def test_restore_raises_on_load_failure(neo4j_handler: Neo4jHandler) -> None:
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (1, "Error: load failed")

    with pytest.raises(RuntimeError, match="neo4j-admin load failed"):
        neo4j_handler.restore("2026-02-19_02-00-00")


def test_restore_cleans_up_temp_container(neo4j_handler: Neo4jHandler) -> None:
    """Temp restore container is removed even on failure."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (1, "Error: load failed")

    with pytest.raises(RuntimeError):
        neo4j_handler.restore("2026-02-19_02-00-00")

    docker.remove_container.assert_called_once()


def test_backup_upload_failure_still_cleans_up(neo4j_handler: Neo4jHandler) -> None:
    """When upload_file fails, temp container is still cleaned up."""
    docker = neo4j_handler._docker
    docker.start_and_wait.return_value = (0, "OK")

    def fake_copy_from(container: str, src: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"NEO4J DUMP")

    docker.copy_from_container.side_effect = fake_copy_from
    neo4j_handler._s3.upload_file.side_effect = RuntimeError("S3 upload failed")

    with pytest.raises(RuntimeError, match="S3 upload failed"):
        neo4j_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    docker.remove_container.assert_called_once()
