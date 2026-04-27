from typing import override

from sqlalchemy import Engine

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult
from swiss_ai_hub.backup.maintenance.dagster_cleanup_sql import execute_capped_delete

_LABEL = "dagster_debug_logs"
_WHERE = "dagster_event_type IS NULL AND event::jsonb->>'level' = '10'"


class DagsterDebugLogsHandler(MaintenanceHandler):
    """Delete Python DEBUG (level=10) log entries from event_logs older than the configured retention.

    Targets only rows where ``dagster_event_type IS NULL`` — those are
    user-emitted Python logger entries, not Dagster framework events. Asset
    materializations, step start/success, and other framework events are
    not touched.
    """

    def __init__(self, engine: Engine, delete_after_days: int, batch_limit: int) -> None:
        self._engine = engine
        self._delete_after_days = delete_after_days
        self._batch_limit = batch_limit

    @property
    @override
    def service_name(self) -> str:
        return _LABEL

    @override
    def run(self) -> MaintenanceResult:
        try:
            rows, duration = execute_capped_delete(
                self._engine, _LABEL, _WHERE, self._delete_after_days, self._batch_limit
            )
        except Exception as e:
            return MaintenanceResult(name=_LABEL, succeeded=False, error=str(e))
        return MaintenanceResult(
            name=_LABEL,
            succeeded=True,
            duration_seconds=round(duration, 1),
            rows_affected=rows,
            metadata={"retention_days": self._delete_after_days, "batch_limit": self._batch_limit},
        )
