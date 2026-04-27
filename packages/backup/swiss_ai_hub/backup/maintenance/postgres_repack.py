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


def _is_missing_extension_error(stderr: str) -> bool:
    """True when pg_repack's stderr indicates the server-side extension is missing.

    Tighter than the previous "extension OR does not exist" heuristic — we
    require both signals together, OR the explicit "is not installed" wording
    pg_repack uses for the missing-extension case. Errors like
    ``relation "event_logs" does not exist`` (table missing) or
    ``column ... does not exist`` (Postgres version mismatch) are NO LONGER
    silently classified as "skip — no extension"; they fail loudly so
    operators see them.
    """
    s = stderr.lower()
    if "is not installed" in s:
        return True
    return "extension" in s and "does not exist" in s


class PostgresRepackHandler(MaintenanceHandler):
    """Run pg_repack on the heavy Dagster tables to return disk space to the OS.

    pg_repack rewrites tables online with minimal lock contention. Plain
    VACUUM (even autovacuum) only marks dead rows reusable internally; it
    does not return pages to the OS. Without periodic repack, the on-disk
    size never decreases even if many rows are deleted.

    Skip-rather-than-fail behavior: if the ``pg_repack`` binary or extension
    is not installed on this deployment, the handler returns a SKIPPED result
    rather than failing — operators can install pg_repack later without
    rebuilding the maintenance image. Any OTHER subprocess error (timeout,
    real SQL failure) is reported as ``succeeded=False`` to honor the
    per-handler failure-isolation contract.
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
            # Parity with SQLAlchemy application_name so DBAs see consistent
            # labels in pg_stat_activity across all maintenance connections.
            "PGAPPNAME": "swiss-ai-hub-maintenance",
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
            except subprocess.TimeoutExpired:
                duration = time.monotonic() - start
                logger.error("[%s] pg_repack %s timed out after %ds", _LABEL, table, _REPACK_TIMEOUT)
                return MaintenanceResult(
                    name=_LABEL,
                    succeeded=False,
                    duration_seconds=round(duration, 1),
                    error=f"pg_repack {table} timed out after {_REPACK_TIMEOUT}s",
                )
            except subprocess.CalledProcessError as e:
                stderr = (e.stderr or "").strip()
                if _is_missing_extension_error(stderr):
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
