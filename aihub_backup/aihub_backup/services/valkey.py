import logging
import shutil
import tempfile
import time
from pathlib import Path
from typing import override

from aihub_backup.docker_client import DockerManager
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

# Maximum seconds to wait for BGSAVE to complete
BGSAVE_TIMEOUT = 120


class ValkeyHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager, docker: DockerManager) -> None:
        self._settings = settings
        self._s3 = s3
        self._docker = docker

    @property
    @override
    def service_name(self) -> str:
        return "Valkey"

    @override
    def backup(self, timestamp: str, prefix: str) -> None:
        container = self._settings.VALKEY_CONTAINER
        password = self._settings.REDIS_TOKEN.get_secret_value()
        s3_key = f"{prefix}/valkey.rdb"

        if not self._docker.container_is_running(container):
            raise RuntimeError(f"Valkey container '{container}' is not running")

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-valkey-"))
        rdb_file = tmp_dir / "valkey.rdb"

        try:
            last_save_before = self._exec_cli(container, password, "LASTSAVE")

            logger.info("Triggering BGSAVE...")
            bgsave_output = self._exec_cli(container, password, "BGSAVE")

            if "already in progress" in bgsave_output.lower():
                logger.info("BGSAVE already in progress, waiting for completion...")

            self._wait_for_bgsave(container, password, last_save_before)

            logger.info("Copying dump.rdb from container...")
            self._docker.copy_from_container(container, "/data/dump.rdb", rdb_file)

            size_mb = rdb_file.stat().st_size / (1024 * 1024)
            logger.info("Dump size: %.1fMB", size_mb)

            self._s3.upload_file(rdb_file, s3_key)
            logger.info("Valkey: done")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, timestamp: str) -> None:
        container = self._settings.VALKEY_CONTAINER
        s3_key = f"{timestamp}/valkey.rdb"

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-valkey-"))
        rdb_file = tmp_dir / "valkey.rdb"

        try:
            self._s3.download_file(s3_key, rdb_file)

            # Clean up data while container is still running (exec requires it)
            if self._docker.container_is_running(container):
                logger.info("Clearing existing data files...")
                self._docker.exec_in_container(container, ["rm", "-rf", "/data/appendonlydir"])
                self._docker.exec_in_container(container, ["rm", "-rf", "/data/dump.rdb"])

            logger.info("Stopping Valkey for RDB restore...")
            self._docker.stop_container(container)

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

    def _exec_cli(self, container: str, password: str, *args: str) -> str:
        exit_code, output = self._docker.exec_in_container(
            container,
            ["valkey-cli", "--no-auth-warning", *args],
            environment={"REDISCLI_AUTH": password},
        )
        if exit_code != 0:
            raise RuntimeError(f"valkey-cli {' '.join(args)} failed: {output}")
        return output.strip()

    def _wait_for_bgsave(self, container: str, password: str, last_save_before: str) -> None:
        start = time.monotonic()
        deadline = start + BGSAVE_TIMEOUT
        while time.monotonic() < deadline:
            time.sleep(2)
            last_save_now = self._exec_cli(container, password, "LASTSAVE")
            if last_save_now != last_save_before:
                logger.info("BGSAVE completed in ~%ds", int(time.monotonic() - start))
                return

        raise RuntimeError(f"BGSAVE did not complete within {BGSAVE_TIMEOUT}s")
