import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import override

from pymilvus import MilvusClient

from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

CONFIG_SOURCE = Path("/etc/backup/milvus-backup.yaml")

# Timeouts for milvus-backup subprocess calls (seconds)
MILVUS_BACKUP_TIMEOUT = 1800  # 30 min for create/restore
MILVUS_LIST_TIMEOUT = 60  # 1 min for list

# subprocess.run(env=...) replaces the entire environment; without an
# explicit PATH the milvus-backup binary would not be found.
_MILVUS_ENV: dict[str, str] = {"PATH": "/usr/local/bin:/usr/bin:/bin"}


class MilvusHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager) -> None:
        self._settings = settings
        self._s3 = s3

    @property
    @override
    def service_name(self) -> str:
        return "Milvus"

    @override
    def backup(self, backup_id: str, s3_prefix: str) -> None:
        backup_name = f"milvus_backup_{backup_id.replace('-', '_')}"

        workdir = Path(tempfile.mkdtemp(prefix="backup-milvus-"))
        try:
            self._prepare_workdir(s3_prefix, workdir)

            logger.info("Creating Milvus backup: %s...", backup_name)
            result = subprocess.run(
                ["milvus-backup", "create", "-n", backup_name],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                check=False,
                timeout=MILVUS_BACKUP_TIMEOUT,
                env=_MILVUS_ENV,
            )
            if result.returncode != 0:
                raise RuntimeError(f"milvus-backup create failed (exit {result.returncode}): {result.stderr.strip()}")
            logger.info("Milvus backup written directly to S3")

            result = subprocess.run(
                ["milvus-backup", "list"],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                check=False,
                timeout=MILVUS_LIST_TIMEOUT,
                env=_MILVUS_ENV,
            )
            if result.stdout:
                for line in result.stdout.strip().split("\n")[-5:]:
                    logger.info("  %s", line)

            self._verify_backup_or_raise(s3_prefix, backup_name)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    @override
    def restore(self, backup_prefix: str) -> None:
        """After restore, collections have schemas and indexes but are NOT loaded
        into memory — applications must call load_collection() on startup.
        """
        workdir = Path(tempfile.mkdtemp(prefix="backup-milvus-"))
        try:
            self._prepare_workdir(backup_prefix, workdir)

            prefixes = self._s3.list_prefixes(f"{backup_prefix}/")
            backup_names = [p.split("/")[-1] for p in prefixes if "milvus_backup_" in p]
            if not backup_names:
                raise RuntimeError(f"No milvus-backup found in s3://{self._s3.bucket}/{backup_prefix}/")

            self._drop_all_collections()

            backup_name = sorted(backup_names)[-1]
            logger.info("Restoring Milvus backup: %s from %s", backup_name, backup_prefix)

            result = subprocess.run(
                ["milvus-backup", "restore", "-n", backup_name, "--rebuild_index", "--drop_exist_collection"],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                check=False,
                timeout=MILVUS_BACKUP_TIMEOUT,
                env=_MILVUS_ENV,
            )
            if result.returncode != 0:
                raise RuntimeError(f"milvus-backup restore failed (exit {result.returncode}): {result.stderr.strip()}")

            result = subprocess.run(
                ["milvus-backup", "list"],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                check=False,
                timeout=MILVUS_LIST_TIMEOUT,
                env=_MILVUS_ENV,
            )
            if result.stdout:
                for line in result.stdout.strip().split("\n")[-5:]:
                    logger.info("  %s", line)

            logger.info("Milvus restore complete")
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    def _drop_all_collections(self) -> None:
        """Ensure restore produces an exact replica.

        Collections created after the backup would otherwise survive,
        since milvus-backup only drops conflicting names.
        """

        client = MilvusClient(
            uri=f"http://{self._settings.MILVUS_HOST}:{self._settings.MILVUS_PORT}",
            token=f"root:{self._settings.MILVUS_ROOT_PASSWORD.get_secret_value()}",
        )
        collections = client.list_collections()
        for name in collections:
            logger.info("  Dropping collection: %s", name)
            client.drop_collection(name)
        logger.info("Dropped %d existing collection(s)", len(collections))

    def _prepare_workdir(self, backup_root_path: str, workdir: Path) -> None:
        config_dir = workdir / "configs"
        config_dir.mkdir(parents=True)

        config_text = CONFIG_SOURCE.read_text()
        config_text = config_text.replace(
            "${MILVUS_ROOT_PASSWORD}", self._yaml_escape(self._settings.MILVUS_ROOT_PASSWORD.get_secret_value())
        )
        config_text = config_text.replace(
            "${AWS_ACCESS_KEY_ID}", self._yaml_escape(self._settings.S3_STORAGE_ACCESS_KEY)
        )
        config_text = config_text.replace(
            "${AWS_SECRET_ACCESS_KEY}", self._yaml_escape(self._settings.S3_STORAGE_SECRET_KEY.get_secret_value())
        )
        config_text = config_text.replace("${BACKUP_ROOT_PATH}", self._yaml_escape(backup_root_path))
        config_text = config_text.replace("${BACKUP_S3_BUCKET}", self._yaml_escape(self._settings.BACKUP_S3_BUCKET))

        config_file = config_dir / "backup.yaml"
        config_file.write_text(config_text)
        config_file.chmod(0o600)

    def _verify_backup_or_raise(self, prefix: str, backup_name: str) -> None:
        """Post-backup integrity check.

        Downloads full_meta.json and verifies every non-L0 segment has insert
        logs. Catches the silent corruption bug where GC deletes segment data
        during backup but milvus-backup still reports success.

        See: https://github.com/zilliztech/milvus-backup/issues/541
             https://github.com/zilliztech/milvus-backup/pull/950
        """
        meta_key = f"{prefix}/{backup_name}/meta/full_meta.json"
        with tempfile.NamedTemporaryFile(prefix="milvus-verify-meta-", suffix=".json", delete=False) as tmp:
            meta_path = Path(tmp.name)

        try:
            if not self._s3.file_exists(meta_key):
                raise RuntimeError(
                    f"Milvus backup metadata not found at {meta_key} -- milvus-backup likely failed silently"
                )

            self._s3.download_file(meta_key, meta_path)
            if not self._verify_milvus_meta(meta_path):
                raise RuntimeError("Milvus backup integrity check failed: segments with missing insert logs")
        finally:
            meta_path.unlink(missing_ok=True)

    @staticmethod
    def _yaml_escape(value: str) -> str:
        """Escape special characters for safe YAML double-quoted string substitution."""
        return (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )

    @staticmethod
    def _verify_milvus_meta(meta_path: Path) -> bool:
        with open(meta_path) as f:
            meta = json.load(f)

        collections = meta.get("collection_backups", [])
        if not collections:
            logger.info("Integrity check passed: no collections to verify (empty Milvus)")
            return True

        total_segments = 0
        empty_segments: list[str] = []

        for coll in collections:
            coll_name = coll.get("collection_name", coll.get("collection_id", "?"))
            db_name = coll.get("db_name", "default")

            for partition in coll.get("partition_backups", []):
                for seg in partition.get("segment_backups", []):
                    if seg.get("is_l0", False):
                        continue

                    total_segments += 1
                    binlogs = seg.get("binlogs", [])
                    has_data = any(len(field.get("binlogs", [])) > 0 for field in binlogs)

                    if not has_data:
                        empty_segments.append(
                            f"  segment {seg.get('segment_id', '?')} "
                            f"(collection={db_name}.{coll_name}, "
                            f"partition={partition.get('partition_name', '?')}, "
                            f"rows={seg.get('num_of_rows', '?')})"
                        )

            # L0 segments only have delta logs — count but don't check
            for _ in coll.get("l0_segments", []):
                total_segments += 1

        if empty_segments:
            logger.error(
                "INTEGRITY CHECK FAILED: %d segment(s) have no insert logs (likely GC'd during backup)",
                len(empty_segments),
            )
            for line in empty_segments:
                logger.error(line)
            return False

        logger.info("Integrity check passed: %d segment(s) verified", total_segments)
        return True
