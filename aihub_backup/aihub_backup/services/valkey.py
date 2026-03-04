import logging
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import override

import redis

from aihub_backup.docker_client import DockerManager
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

BGSAVE_TIMEOUT = 120


class ValkeyHandler(BackupHandler):
    """Hybrid backup using the Redis protocol and Docker file copy.

    Backup is online: ``BGSAVE`` triggers an RDB snapshot while Valkey keeps
    serving, then the RDB file is copied out of the *running* container.

    Restore requires a brief stop: stale data files (AOF directory + RDB) must
    be removed before the restored snapshot is copied in.  Because the main
    container is stopped at that point and ``docker exec`` needs a running
    process, a temporary sibling container (same image, same ``/data`` volume)
    runs ``rm -rf`` to clean the directory.  After copying the new files in,
    the main container is restarted.
    """

    def __init__(self, settings: BackupSettings, s3: S3Manager, docker: DockerManager) -> None:
        self._settings = settings
        self._s3 = s3
        self._docker = docker

    @property
    @override
    def service_name(self) -> str:
        return "Valkey"

    @override
    def backup(self, backup_id: str, s3_prefix: str) -> None:
        container = self._settings.VALKEY_CONTAINER
        s3_key = f"{s3_prefix}/valkey.rdb"

        if not self._docker.container_is_running(container):
            raise RuntimeError(f"Valkey container '{container}' is not running")

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-valkey-"))
        rdb_file = tmp_dir / "valkey.rdb"

        try:
            client = self._create_client()
            last_save_before = client.lastsave()

            logger.info("Triggering BGSAVE...")
            try:
                client.bgsave()
            except redis.exceptions.ResponseError as e:
                if "already in progress" in str(e).lower():
                    logger.info("BGSAVE already in progress, waiting for completion...")
                else:
                    raise

            self._wait_for_bgsave_or_raise(client, last_save_before)

            logger.info("Copying dump.rdb from container...")
            self._docker.copy_from_container(container, "/data/dump.rdb", rdb_file)

            size_mb = rdb_file.stat().st_size / (1024 * 1024)
            logger.info("Dump size: %.1fMB", size_mb)

            self._s3.upload_file(rdb_file, s3_key)
            logger.info("Valkey: done")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, backup_prefix: str) -> None:
        container = self._settings.VALKEY_CONTAINER
        s3_key = f"{backup_prefix}/valkey.rdb"

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-valkey-"))
        rdb_file = tmp_dir / "valkey.rdb"

        try:
            self._s3.download_file(s3_key, rdb_file)

            # Build an AOF directory structure that uses the backup RDB as the
            # base file. Valkey's multi-part AOF loads the base RDB first and then
            # replays incremental AOF entries on top. By providing the restored RDB
            # as the base and an empty incremental file, Valkey starts with exactly
            # the backed-up state.
            logger.info("Preparing AOF directory with restored RDB as base...")
            aof_dir = tmp_dir / "appendonlydir"
            aof_dir.mkdir()
            shutil.copy2(rdb_file, aof_dir / "appendonly.aof.1.base.rdb")
            (aof_dir / "appendonly.aof.1.incr.aof").touch()
            (aof_dir / "appendonly.aof.manifest").write_text(
                "file appendonly.aof.1.base.rdb seq 1 type b\nfile appendonly.aof.1.incr.aof seq 1 type i\n"
            )

            logger.info("Stopping Valkey for RDB restore...")
            self._docker.stop_container(container)

            logger.info("Clearing existing data files via temp container...")
            self._clean_data_via_temp_container(container)

            logger.info("Copying restored data into container...")
            self._docker.copy_to_container(container, aof_dir, "/data/appendonlydir")
            self._docker.copy_to_container(container, rdb_file, "/data/dump.rdb")

            logger.info("Starting Valkey...")
            self._docker.start_container(container)
            if not self._docker.wait_for_healthy(container, timeout=60):
                raise RuntimeError(f"Valkey container '{container}' did not become healthy after restore")

            logger.info("Valkey restore complete")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _clean_data_via_temp_container(self, container: str) -> None:
        """Remove stale data files using a temp sibling container sharing the data volume.

        Works regardless of whether the main container is running — unlike
        exec_in_container which requires a running container.
        """
        image, data_mount = self._resolve_image_and_data_mount(container)
        cleanup_name = f"valkey-cleanup-{uuid.uuid4().hex[:8]}"
        try:
            self._docker.create_container(
                name=cleanup_name,
                image=image,
                command=["rm", "-rf", "/data/appendonlydir", "/data/dump.rdb"],
                volumes={data_mount: {"bind": "/data", "mode": "rw"}},
            )
            exit_code, logs = self._docker.start_and_wait(cleanup_name)
            if exit_code != 0:
                raise RuntimeError(f"Valkey data cleanup failed (exit {exit_code}): {logs}")
        finally:
            try:
                self._docker.remove_container(cleanup_name)
            except Exception:
                logger.warning("Failed to remove temp container %s", cleanup_name, exc_info=True)

    def _resolve_image_and_data_mount(self, container: str) -> tuple[str, str]:
        if not self._docker.container_exists(container):
            raise RuntimeError(f"Valkey container '{container}' not found")
        image = self._docker.get_container_image(container)
        data_mount = self._docker.get_volume_mount(container, "/data")
        if not data_mount or not image:
            raise RuntimeError("Could not determine Valkey image or /data volume mount")
        return image, data_mount

    def _create_client(self) -> redis.Redis:
        return redis.Redis(
            host=self._settings.VALKEY_HOST,
            port=self._settings.VALKEY_PORT,
            password=self._settings.REDIS_TOKEN.get_secret_value(),
        )

    def _wait_for_bgsave_or_raise(self, client: redis.Redis, last_save_before: object) -> None:
        start = time.monotonic()
        deadline = start + BGSAVE_TIMEOUT
        while time.monotonic() < deadline:
            time.sleep(2)
            last_save_now = client.lastsave()
            if last_save_now != last_save_before:
                logger.info("BGSAVE completed in ~%ds", int(time.monotonic() - start))
                return

        raise RuntimeError(f"BGSAVE did not complete within {BGSAVE_TIMEOUT}s")
