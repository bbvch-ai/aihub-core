import logging
import shutil
import subprocess
import time
from typing import override

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult
from swiss_ai_hub.backup.settings import BackupSettings

logger = logging.getLogger(__name__)
_LABEL = "postgres_repack"
_REPACK_TIMEOUT = 7200  # 2 hours per table — large event_logs can take a while
_REPACK_TABLES = ("event_logs", "runs", "job_ticks")


class PostgresRepackHandler(MaintenanceHandler):
    """Run pg_repack on the heavy Dagster tables to return disk space to the OS.

    pg_repack rewrites tables online with minimal lock contention. Plain
    VACUUM (even autovacuum) only marks dead rows reusable internally; it
    does not return pages to the OS. Without periodic repack, the on-disk
    size never decreases even if many rows are deleted.

    Skip-rather-than-fail behavior: if the ``pg_repack`` binary or extension
    is not installed on this deployment, the handler returns a SKIPPED result
    rather than failing — operators can install pg_repack later without
    rebuilding the maintenance image.
    """

    def __init__(self, settings: BackupSettings) -> None:
        self._settings = settings

    @property
    @override
    def service_name(self) -> str:
        return _LABEL

    @override
    def run(self) -> MaintenanceResult:
        binary = shutil.which("pg_repack")
        if binary is None:
            logger.warning("[%s] pg_repack binary not found — skipping. Install pg_repack to enable.", _LABEL)
            return MaintenanceResult(
                name=_LABEL,
                succeeded=True,
                duration_seconds=0.0,
                metadata={"skipped": "pg_repack binary not installed"},
            )

        start = time.monotonic()
        repacked: list[str] = []
        skipped: list[str] = []
        env = {
            "PGPASSWORD": self._settings.POSTGRES_PASSWORD.get_secret_value(),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        }
        for table in _REPACK_TABLES:
            try:
                subprocess.run(
                    [
                        binary,
                        "-h",
                        self._settings.MAINTENANCE_POSTGRES_HOST,
                        "-p",
                        str(self._settings.MAINTENANCE_POSTGRES_PORT),
                        "-U",
                        self._settings.POSTGRES_USER,
                        "-d",
                        self._settings.MAINTENANCE_DAGSTER_DB,
                        "-t",
                        table,
                        "--no-superuser-check",
                    ],
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=_REPACK_TIMEOUT,
                )
                repacked.append(table)
                logger.info("[%s] Repacked %s", _LABEL, table)
            except subprocess.CalledProcessError as e:
                stderr = (e.stderr or "").strip()
                if "extension" in stderr.lower() or "does not exist" in stderr.lower():
                    skipped.append(f"{table} (no extension)")
                    logger.warning("[%s] pg_repack extension not installed on server — skipping %s", _LABEL, table)
                    continue
                duration = time.monotonic() - start
                return MaintenanceResult(
                    name=_LABEL,
                    succeeded=False,
                    duration_seconds=round(duration, 1),
                    error=f"pg_repack {table} failed: {stderr[:500]}",
                )

        duration = time.monotonic() - start
        return MaintenanceResult(
            name=_LABEL,
            succeeded=True,
            duration_seconds=round(duration, 1),
            metadata={
                "repacked": ", ".join(repacked) if repacked else "none",
                "skipped": ", ".join(skipped) if skipped else "none",
            },
        )
