import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import override

from docker.errors import APIError

from swiss_ai_hub.backup.docker_client import DockerManager
from swiss_ai_hub.backup.s3 import S3Manager
from swiss_ai_hub.backup.services.base import BackupHandler
from swiss_ai_hub.backup.settings import BackupSettings

logger = logging.getLogger(__name__)


class Neo4jHandler(BackupHandler):
    """Offline backup via a temporary sibling container.

    Neo4j Community Edition only supports ``neo4j-admin database dump/load``,
    which requires exclusive access to the ``/data`` directory. The main
    container is stopped globally by ``backup_session`` / ``restore_session``,
    so a short-lived sibling container (same image, same /data volume) is used
    to run the dump/load commands.
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
    def backup(self, backup_id: str, s3_prefix: str) -> None:
        s3_key = f"{s3_prefix}/neo4j.dump"
        image, data_mount = self._resolve_image_and_data_mount()

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-neo4j-"))
        dump_file = tmp_dir / "neo4j.dump"
        dump_container_name = f"neo4j-dump-{uuid.uuid4().hex[:8]}"

        try:
            self._run_dump(image, data_mount, dump_container_name, dump_file)

            size_mb = dump_file.stat().st_size / (1024 * 1024)
            logger.info("Dump size: %.1fMB", size_mb)

            self._s3.upload_file(dump_file, s3_key)
            logger.info("Neo4j: done")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            try:
                self._docker.remove_container(dump_container_name)
            except APIError:
                logger.warning("Failed to remove temp container %s during cleanup", dump_container_name, exc_info=True)

    @override
    def restore(self, backup_prefix: str) -> None:
        s3_key = f"{backup_prefix}/neo4j.dump"
        image, data_mount = self._resolve_image_and_data_mount()

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-neo4j-"))
        dump_file = tmp_dir / "neo4j.dump"
        restore_container_name = f"neo4j-restore-{uuid.uuid4().hex[:8]}"

        try:
            self._s3.download_file(s3_key, dump_file)
            self._run_load(image, data_mount, restore_container_name, dump_file)
            logger.info("Neo4j restore complete")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            try:
                self._docker.remove_container(restore_container_name)
            except APIError:
                logger.warning(
                    "Failed to remove temp container %s during cleanup", restore_container_name, exc_info=True
                )

    def _resolve_image_and_data_mount(self) -> tuple[str, str]:
        container = self._settings.NEO4J_CONTAINER
        if not self._docker.container_exists(container):
            raise RuntimeError(f"Neo4j container '{container}' not found")

        image = self._docker.get_container_image(container)
        data_mount = self._docker.get_volume_mount(container, "/data")
        if not data_mount or not image:
            raise RuntimeError("Could not determine Neo4j image or /data volume mount")
        return image, data_mount

    def _run_dump(self, image: str, data_mount: str, container_name: str, dump_file: Path) -> None:
        logger.info("Running neo4j-admin database dump...")
        self._docker.create_container(
            name=container_name,
            image=image,
            command=["neo4j-admin", "database", "dump", "neo4j", "--to-path=/tmp", "--verbose"],
            volumes={data_mount: {"bind": "/data", "mode": "rw"}},
        )
        exit_code, logs = self._docker.start_and_wait(container_name)
        if exit_code != 0:
            raise RuntimeError(f"neo4j-admin dump failed (exit {exit_code}): {logs}")

        self._docker.copy_from_container(container_name, "/tmp/neo4j.dump", dump_file)

    def _run_load(self, image: str, data_mount: str, container_name: str, dump_file: Path) -> None:
        logger.info("Loading dump via neo4j-admin database load...")
        self._docker.create_container(
            name=container_name,
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
        self._docker.copy_to_container(container_name, dump_file, "/tmp/neo4j.dump")
        exit_code, logs = self._docker.start_and_wait(container_name)
        if exit_code != 0:
            raise RuntimeError(f"neo4j-admin load failed (exit {exit_code}): {logs}")
