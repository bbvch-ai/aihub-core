import logging
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import override

from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

# Timeouts for nats CLI subprocess calls (seconds)
NATS_LIST_TIMEOUT = 30
NATS_STREAM_TIMEOUT = 120  # stream backup/restore can be slow


class NatsHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager) -> None:
        self._settings = settings
        self._s3 = s3

    @property
    @override
    def service_name(self) -> str:
        return "NATS"

    @override
    def backup(self, timestamp: str, prefix: str) -> None:
        s3_key = f"{prefix}/nats-jetstream.tar.gz"

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-nats-"))
        backup_dir = tmp_dir / "nats-backup"
        tar_file = tmp_dir / "nats-jetstream.tar.gz"
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            stream_names = self._list_streams()
            if not stream_names:
                logger.info("No JetStream streams found, creating empty backup archive")
            else:
                logger.info("Found %d JetStream stream(s): %s", len(stream_names), ", ".join(stream_names))

                for stream_name in stream_names:
                    stream_backup_path = backup_dir / stream_name
                    logger.info("Backing up stream: %s", stream_name)
                    self._run_nats(["stream", "backup", stream_name, str(stream_backup_path)])

            logger.info("Compressing...")
            with tarfile.open(tar_file, "w:gz") as tar:
                tar.add(str(backup_dir), arcname="nats-backup")

            size_mb = tar_file.stat().st_size / (1024 * 1024)
            logger.info("Archive size: %.1fMB", size_mb)

            self._s3.upload_file(tar_file, s3_key)
            logger.info("NATS: done")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, timestamp: str) -> None:
        s3_key = f"{timestamp}/nats-jetstream.tar.gz"

        if not self._s3.file_exists(s3_key):
            logger.info("No NATS JetStream backup found in %s, skipping restore", timestamp)
            return

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-nats-"))
        tar_file = tmp_dir / "nats-jetstream.tar.gz"

        try:
            self._s3.download_file(s3_key, tar_file)

            logger.info("Extracting archive...")
            with tarfile.open(tar_file, "r:gz") as tar:
                tar.extractall(tmp_dir, filter="data")

            backup_dir = tmp_dir / "nats-backup"
            if not backup_dir.exists():
                raise RuntimeError("No nats-backup directory found in archive")

            stream_dirs = sorted((d for d in backup_dir.iterdir() if d.is_dir()), key=lambda d: d.name)

            # Delete existing streams that would conflict with restore
            existing_streams = set(self._list_streams())
            for stream_dir in stream_dirs:
                if stream_dir.name in existing_streams:
                    logger.info("Deleting existing stream before restore: %s", stream_dir.name)
                    self._run_nats(["stream", "rm", stream_dir.name, "-f"])

            for stream_dir in stream_dirs:
                logger.info("Restoring stream: %s", stream_dir.name)
                self._run_nats(["stream", "restore", str(stream_dir)])

            logger.info("NATS restore complete (%d stream(s))", len(stream_dirs))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _nats_base_args(self) -> list[str]:
        return ["nats", "-s", self._settings.NATS_URL]

    def _nats_env(self) -> dict[str, str]:
        """subprocess.run(env=...) replaces the entire environment; PATH must
        be explicit and NATS_TOKEN is read by the nats CLI for auth.
        """
        return {
            "NATS_TOKEN": self._settings.NATS_TOKEN.get_secret_value(),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        }

    def _list_streams(self) -> list[str]:
        result = subprocess.run(
            [*self._nats_base_args(), "stream", "list", "--names"],
            capture_output=True,
            text=True,
            check=False,
            env=self._nats_env(),
            timeout=NATS_LIST_TIMEOUT,
        )
        if result.returncode == 0:
            if not result.stdout.strip():
                return []
            return [name.strip() for name in result.stdout.strip().split("\n") if name.strip()]

        # Non-zero exit: distinguish "no streams" from actual errors
        stderr = result.stderr.lower() if result.stderr else ""
        if "no streams" in stderr or "no jetstream" in stderr:
            return []
        raise RuntimeError(f"nats stream list failed (exit {result.returncode}): {result.stderr}")

    def _run_nats(self, args: list[str]) -> str:
        result = subprocess.run(
            [*self._nats_base_args(), *args],
            capture_output=True,
            text=True,
            check=False,
            env=self._nats_env(),
            timeout=NATS_STREAM_TIMEOUT,
        )
        if result.returncode != 0:
            raise RuntimeError(f"nats {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}")
        return result.stdout
