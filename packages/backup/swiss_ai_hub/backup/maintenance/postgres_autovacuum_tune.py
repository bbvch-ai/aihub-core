import logging
import time
from typing import override

from sqlalchemy import Engine, text

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult

logger = logging.getLogger(__name__)
_LABEL = "postgres_autovacuum_tune"

# Default Postgres autovacuum kicks in at 20% dead tuples — on a 100+ GiB
# event_logs table that means 20+ GiB of dead rows accumulate before vacuum
# fires, often timing out and falling further behind. Tighter thresholds
# trigger more frequent, smaller vacuums that keep up.
# Idempotent: ALTER TABLE SET is a no-op if the same value is already set.
_TABLE_TUNINGS: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "event_logs",
        {
            "autovacuum_vacuum_scale_factor": "0.05",
            "autovacuum_analyze_scale_factor": "0.02",
        },
    ),
    (
        "runs",
        {"autovacuum_vacuum_scale_factor": "0.10"},
    ),
)


class PostgresAutovacuumTuneHandler(MaintenanceHandler):
    """Idempotent ALTER TABLE to apply per-table autovacuum tuning.

    Runs every weekly cleanup. Per-table reloptions override the cluster
    default, persist across restarts, and only affect the specified tables.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @property
    @override
    def service_name(self) -> str:
        return _LABEL

    @override
    def run(self) -> MaintenanceResult:
        start = time.monotonic()
        applied: list[str] = []
        try:
            with self._engine.begin() as conn:
                existing = self._existing_tables(conn)
                for table, options in _TABLE_TUNINGS:
                    if table not in existing:
                        logger.info("[%s] Skipping %s — table not present", _LABEL, table)
                        continue
                    settings = ", ".join(f"{k} = {v}" for k, v in options.items())
                    conn.execute(text(f"ALTER TABLE {table} SET ({settings})"))
                    applied.append(table)
                    logger.info("[%s] Applied tuning to %s: %s", _LABEL, table, settings)
        except Exception as e:
            return MaintenanceResult(name=_LABEL, succeeded=False, error=str(e))
        duration = time.monotonic() - start
        return MaintenanceResult(
            name=_LABEL,
            succeeded=True,
            duration_seconds=round(duration, 1),
            metadata={"tables_tuned": ", ".join(applied) if applied else "none"},
        )

    @staticmethod
    def _existing_tables(conn) -> set[str]:
        rows = conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"),
        ).all()
        return {r[0] for r in rows}
