import gzip
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import override

from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)


class PostgresHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager) -> None:
        self._settings = settings
        self._s3 = s3

    @property
    @override
    def service_name(self) -> str:
        return "PostgreSQL"

    @override
    def backup(self, timestamp: str, prefix: str) -> None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-postgres-"))
        try:
            self._backup_host(
                host=self._settings.POSTGRES_HOST,
                user=self._settings.POSTGRES_USER,
                password=self._settings.PGPASSWORD.get_secret_value(),
                label="postgres-main",
                prefix=prefix,
                tmp_dir=tmp_dir,
            )
            self._backup_host(
                host=self._settings.POSTGRES_FERRETDB_HOST,
                user=self._settings.POSTGRES_FERRETDB_USER,
                password=self._settings.PGPASSWORD_FERRETDB.get_secret_value(),
                label="postgres-ferretdb",
                prefix=prefix,
                tmp_dir=tmp_dir,
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, timestamp: str) -> None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-postgres-"))
        try:
            self._restore_host(
                host=self._settings.POSTGRES_HOST,
                user=self._settings.POSTGRES_USER,
                password=self._settings.PGPASSWORD.get_secret_value(),
                label="postgres-main",
                timestamp=timestamp,
                tmp_dir=tmp_dir,
            )
            self._restore_host(
                host=self._settings.POSTGRES_FERRETDB_HOST,
                user=self._settings.POSTGRES_FERRETDB_USER,
                password=self._settings.PGPASSWORD_FERRETDB.get_secret_value(),
                label="postgres-ferretdb",
                timestamp=timestamp,
                tmp_dir=tmp_dir,
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _backup_host(self, host: str, user: str, password: str, label: str, prefix: str, tmp_dir: Path) -> None:
        dump_file = tmp_dir / f"{label}.sql.gz"
        s3_key = f"{prefix}/{label}.sql.gz"

        logger.info("Dumping %s (%s)...", label, host)
        with gzip.open(dump_file, "wb") as f:
            with subprocess.Popen(
                ["pg_dumpall", "-h", host, "-U", user, "--clean", "--if-exists"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={"PGPASSWORD": password, "PATH": "/usr/local/bin:/usr/bin:/bin"},
            ) as proc:
                shutil.copyfileobj(proc.stdout, f)  # type: ignore[arg-type]
                proc.wait()
                stderr_text = proc.stderr.read().decode() if proc.stderr else ""
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(proc.returncode, "pg_dumpall", stderr=stderr_text)

        size_mb = dump_file.stat().st_size / (1024 * 1024)
        logger.info("Dump size: %.1fMB", size_mb)

        self._s3.upload_file(dump_file, s3_key)
        dump_file.unlink(missing_ok=True)
        logger.info("%s: done", label)

    def _restore_host(self, host: str, user: str, password: str, label: str, timestamp: str, tmp_dir: Path) -> None:
        s3_key = f"{timestamp}/{label}.sql.gz"
        dump_file = tmp_dir / f"{label}.sql.gz"

        self._s3.download_file(s3_key, dump_file)

        logger.info("Restoring %s to %s...", label, host)
        with gzip.open(dump_file, "rb") as f:
            with subprocess.Popen(
                ["psql", "-h", host, "-U", user, "-d", "postgres", "--quiet"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                env={"PGPASSWORD": password, "PATH": "/usr/local/bin:/usr/bin:/bin"},
            ) as proc:
                shutil.copyfileobj(f, proc.stdin)  # type: ignore[arg-type]
                proc.stdin.close()  # type: ignore[union-attr]
                proc.wait()
                stderr_text = proc.stderr.read().decode() if proc.stderr else ""
                if stderr_text:
                    logger.warning("psql warnings for %s: %s", label, stderr_text.strip())
                error_lines = [line for line in stderr_text.splitlines() if line.strip().startswith("ERROR:")]
                if proc.returncode != 0 or error_lines:
                    raise RuntimeError(
                        f"psql restore of {label} failed (exit {proc.returncode}): "
                        + ("\n".join(error_lines) if error_lines else stderr_text)
                    )

        dump_file.unlink(missing_ok=True)
        logger.info("%s: restored", label)
