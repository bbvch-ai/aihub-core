import logging
import re
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import override

from aihub_backup.docker_client import DockerManager
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

_BACKUP_NAME_RE = re.compile(r"^backup_[a-zA-Z0-9_]+$")
_TABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*$")


def _validate_backup_name(name: str) -> str:
    if not _BACKUP_NAME_RE.match(name):
        raise ValueError(f"Invalid ClickHouse backup name: {name!r}")
    return name


class ClickHouseHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager, docker: DockerManager) -> None:
        self._settings = settings
        self._s3 = s3
        self._docker = docker

    @property
    @override
    def service_name(self) -> str:
        return "ClickHouse"

    @override
    def backup(self, timestamp: str, prefix: str) -> None:
        ch_host = self._settings.CLICKHOUSE_HOST
        ch_user = self._settings.CLICKHOUSE_USER
        ch_pass = self._settings.CLICKHOUSE_PASSWORD.get_secret_value()
        ch_env = {"CLICKHOUSE_PASSWORD": ch_pass}
        s3_key = f"{prefix}/clickhouse.tar.gz"
        backup_name = _validate_backup_name(f"backup_{timestamp.replace('-', '_')}")

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-clickhouse-"))
        backup_dir = tmp_dir / "clickhouse"
        tar_file = tmp_dir / "clickhouse.tar.gz"

        try:
            exit_code, _ = self._docker.exec_in_container(
                ch_host,
                ["clickhouse-client", f"--user={ch_user}", "--query=SELECT 1"],
                environment=ch_env,
            )
            if exit_code != 0:
                raise RuntimeError(f"ClickHouse not reachable at container '{ch_host}'")

            exit_code, tables_output = self._docker.exec_in_container(
                ch_host,
                [
                    "clickhouse-client",
                    f"--user={ch_user}",
                    "--query=SELECT name FROM system.tables WHERE database = 'default' "
                    "AND engine NOT IN ('View', 'MaterializedView') FORMAT TSV",
                ],
                environment=ch_env,
            )
            if exit_code != 0:
                raise RuntimeError(f"ClickHouse table listing failed (exit {exit_code}): {tables_output}")
            if not tables_output.strip():
                logger.info("No tables found in ClickHouse default database, skipping")
                return

            logger.info("Creating ClickHouse backup...")

            exit_code, output = self._docker.exec_in_container(
                ch_host,
                [
                    "clickhouse-client",
                    f"--user={ch_user}",
                    f"--query=BACKUP DATABASE default TO Disk('default', '{backup_name}')",
                ],
                environment=ch_env,
            )
            if exit_code != 0:
                raise RuntimeError(f"ClickHouse BACKUP failed: {output}")

            logger.info("Copying backup from container...")
            backup_dir.mkdir(parents=True, exist_ok=True)
            self._docker.copy_from_container(ch_host, f"/var/lib/clickhouse/{backup_name}", backup_dir / backup_name)

            # Remove all backup_* directories to clean up the current backup
            # and any orphans left by previously interrupted runs.
            self._docker.exec_in_container(
                ch_host,
                ["sh", "-c", "rm -rf /var/lib/clickhouse/backup_[0-9][0-9][0-9][0-9]_*"],
            )

            logger.info("Compressing...")
            with tarfile.open(tar_file, "w:gz") as tar:
                tar.add(str(backup_dir), arcname="clickhouse")

            size_mb = tar_file.stat().st_size / (1024 * 1024)
            logger.info("Archive size: %.1fMB", size_mb)

            self._s3.upload_file(tar_file, s3_key)
            logger.info("ClickHouse: done")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, timestamp: str) -> None:
        ch_host = self._settings.CLICKHOUSE_HOST
        ch_user = self._settings.CLICKHOUSE_USER
        ch_pass = self._settings.CLICKHOUSE_PASSWORD.get_secret_value()
        ch_env = {"CLICKHOUSE_PASSWORD": ch_pass}
        s3_key = f"{timestamp}/clickhouse.tar.gz"

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-clickhouse-"))
        tar_file = tmp_dir / "clickhouse.tar.gz"

        try:
            self._s3.download_file(s3_key, tar_file)

            logger.info("Extracting archive...")
            with tarfile.open(tar_file, "r:gz") as tar:
                tar.extractall(tmp_dir, filter="data")

            backup_dir = tmp_dir / "clickhouse"

            # Each archive contains exactly one backup_* directory — sort is
            # defensive; there is always only one entry to pick.
            backup_names = [d.name for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
            if not backup_names:
                raise RuntimeError("No backup directory found in archive")

            backup_name = _validate_backup_name(sorted(backup_names)[0])

            logger.info("Dropping existing tables before restore...")
            exit_code, tables_output = self._docker.exec_in_container(
                ch_host,
                [
                    "clickhouse-client",
                    f"--user={ch_user}",
                    "--query=SELECT name FROM system.tables WHERE database = 'default' "
                    "AND engine NOT IN ('View', 'MaterializedView') FORMAT TSV",
                ],
                environment=ch_env,
            )
            if exit_code == 0 and tables_output.strip():
                for table_name in tables_output.strip().split("\n"):
                    table_name = table_name.strip()
                    if not table_name:
                        continue
                    if not _TABLE_NAME_RE.match(table_name):
                        logger.warning("Skipping table with invalid name: %r", table_name)
                        continue
                    logger.info("  Dropping table: %s", table_name)
                    self._docker.exec_in_container(
                        ch_host,
                        [
                            "clickhouse-client",
                            f"--user={ch_user}",
                            f"--query=DROP TABLE IF EXISTS default.`{table_name}`",
                        ],
                        environment=ch_env,
                    )

            logger.info("Copying backup into container...")
            self._docker.copy_to_container(ch_host, backup_dir / backup_name, f"/var/lib/clickhouse/{backup_name}")

            logger.info("Running RESTORE command...")
            exit_code, output = self._docker.exec_in_container(
                ch_host,
                [
                    "clickhouse-client",
                    f"--user={ch_user}",
                    f"--query=RESTORE DATABASE default FROM Disk('default', '{backup_name}')",
                ],
                environment=ch_env,
            )
            if exit_code != 0:
                raise RuntimeError(f"ClickHouse RESTORE failed: {output}")

            self._docker.exec_in_container(ch_host, ["rm", "-rf", f"/var/lib/clickhouse/{backup_name}"])

            logger.info("ClickHouse restore complete")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
