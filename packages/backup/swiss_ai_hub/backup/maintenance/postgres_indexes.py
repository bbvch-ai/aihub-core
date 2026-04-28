import logging
import time
from typing import override

from sqlalchemy import Engine, text

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult

logger = logging.getLogger(__name__)
_LABEL = "postgres_indexes"

# Two indexes recommended by docs.dagster.io/deployment/troubleshooting/database-tuning.
# Without them, the cleanup DELETEs sequential-scan a 130 GiB table.
# CREATE INDEX CONCURRENTLY does not block writes. ``IF NOT EXISTS`` keeps this
# handler idempotent — it runs every weekly cleanup and is a no-op after the first.
_INDEX_STATEMENTS = (
    (
        "idx_clear_event_logs_user_logs",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clear_event_logs_user_logs "
        "ON event_logs ((event::jsonb ->> 'level'::text), timestamp) "
        "WHERE (dagster_event_type IS NULL)",
    ),
    (
        "idx_clear_event_logs_system_events",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clear_event_logs_system_events "
        "ON event_logs (dagster_event_type, timestamp) "
        "WHERE (dagster_event_type IS NOT NULL)",
    ),
)


class PostgresIndexesHandler(MaintenanceHandler):
    """Idempotent index migration for event_logs.

    Runs every weekly cleanup; first run creates the indexes, subsequent runs
    are no-ops. CREATE INDEX CONCURRENTLY cannot run inside a transaction, so
    we use AUTOCOMMIT isolation.
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
        created: list[str] = []
        try:
            with self._engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                for name, ddl in _INDEX_STATEMENTS:
                    existed = conn.execute(
                        text("SELECT 1 FROM pg_indexes WHERE indexname = :n"),
                        {"n": name},
                    ).first()
                    conn.execute(text(ddl))
                    if not existed:
                        created.append(name)
                        logger.info("[%s] Created index %s", _LABEL, name)
        except Exception as e:
            return MaintenanceResult(name=_LABEL, succeeded=False, error=str(e))
        duration = time.monotonic() - start
        return MaintenanceResult(
            name=_LABEL,
            succeeded=True,
            duration_seconds=round(duration, 1),
            metadata={"indexes_created": ", ".join(created) if created else "none (already present)"},
        )
