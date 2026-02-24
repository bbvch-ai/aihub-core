import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import override

from aihub_backup.docker_client import DockerManager
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)


class Neo4jHandler(BackupHandler):
    """Neo4j Community Edition does not support online backups — the container
    is stopped briefly while neo4j-admin runs against the same data volume
    via a temporary sibling container.
    """

    def __init__(self, settings: BackupSettings, s3: S3Manager, docker: DockerManager) -> None:
        self._settings = settings
        self._s3 = s3
        self._docker = docker

    @property
    @override
    def service_name(self) -> str:
        return "Neo4j"

    @override
    def backup(self, timestamp: str, prefix: str) -> None:
        container = self._settings.NEO4J_CONTAINER
        s3_key = f"{prefix}/neo4j.dump"

        if not self._docker.container_exists(container):
            raise RuntimeError(f"Neo4j container '{container}' not found")

        image = self._docker.get_container_image(container)
        data_mount = self._docker.get_volume_mount(container, "/data")
        if not data_mount or not image:
            raise RuntimeError("Could not determine Neo4j image or /data volume mount")

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-neo4j-"))
        dump_file = tmp_dir / "neo4j.dump"
        dump_container_name = f"neo4j-dump-{uuid.uuid4().hex[:8]}"

        restarted = False
        try:
            logger.info("Stopping Neo4j container...")
            self._docker.stop_container(container)

            logger.info("Running neo4j-admin database dump...")
            self._docker.create_container(
                name=dump_container_name,
                image=image,
                command=["neo4j-admin", "database", "dump", "neo4j", "--to-path=/tmp", "--verbose"],
                volumes={data_mount: {"bind": "/data", "mode": "rw"}},
            )
            exit_code, logs = self._docker.start_and_wait(dump_container_name)

            logger.info("Starting Neo4j container...")
            self._docker.start_container(container)
            if not self._docker.wait_for_healthy(container, timeout=120):
                raise RuntimeError(f"Neo4j container '{container}' did not become healthy after restart")
            restarted = True

            if exit_code != 0:
                self._docker.remove_container(dump_container_name)
                raise RuntimeError(f"neo4j-admin dump failed (exit {exit_code}): {logs}")

            self._docker.copy_from_container(dump_container_name, "/tmp/neo4j.dump", dump_file)
            self._docker.remove_container(dump_container_name)

            size_mb = dump_file.stat().st_size / (1024 * 1024)
            logger.info("Dump size: %.1fMB", size_mb)

            self._s3.upload_file(dump_file, s3_key)
            logger.info("Neo4j: done")
        except Exception:
            if not restarted:
                self._docker.start_container(container)
                if not self._docker.wait_for_healthy(container, timeout=120):
                    logger.warning("Neo4j did not become healthy after error recovery restart")
            try:
                self._docker.remove_container(dump_container_name)
            except Exception:
                logger.warning("Failed to remove temp container %s during cleanup", dump_container_name, exc_info=True)
            raise
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, timestamp: str) -> None:
        container = self._settings.NEO4J_CONTAINER
        s3_key = f"{timestamp}/neo4j.dump"

        if not self._docker.container_exists(container):
            raise RuntimeError(f"Neo4j container '{container}' not found")

        image = self._docker.get_container_image(container)
        data_mount = self._docker.get_volume_mount(container, "/data")
        if not data_mount or not image:
            raise RuntimeError("Could not determine Neo4j image or /data volume mount")

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-neo4j-"))
        dump_file = tmp_dir / "neo4j.dump"
        restore_container_name = f"neo4j-restore-{uuid.uuid4().hex[:8]}"

        restarted = False
        try:
            self._s3.download_file(s3_key, dump_file)

            # Stop Neo4j if running
            self._docker.stop_container(container)

            logger.info("Loading dump via neo4j-admin database load...")
            self._docker.create_container(
                name=restore_container_name,
                image=image,
                command=[
                    "neo4j-admin",
                    "database",
                    "load",
                    "neo4j",
                    "--from-path=/tmp",
                    "--overwrite-destination",
                    "--verbose",
                ],
                volumes={data_mount: {"bind": "/data", "mode": "rw"}},
            )

            # Copy dump into temp container before starting it
            self._docker.copy_to_container(restore_container_name, dump_file, "/tmp/neo4j.dump")

            exit_code, logs = self._docker.start_and_wait(restore_container_name)

            if exit_code != 0:
                raise RuntimeError(f"neo4j-admin load failed (exit {exit_code}): {logs}")

            logger.info("Starting Neo4j...")
            self._docker.start_container(container)
            if not self._docker.wait_for_healthy(container, timeout=120):
                raise RuntimeError(f"Neo4j container '{container}' did not become healthy after restore")
            restarted = True
            logger.info("Neo4j restore complete")
        except Exception:
            if not restarted:
                self._docker.start_container(container)
                if not self._docker.wait_for_healthy(container, timeout=120):
                    logger.warning("Neo4j did not become healthy after error recovery restart")
            raise
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            try:
                self._docker.remove_container(restore_container_name)
            except Exception:
                logger.warning(
                    "Failed to remove temp container %s during cleanup", restore_container_name, exc_info=True
                )
