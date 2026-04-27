from typing import override

from sqlalchemy import Engine

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult
from swiss_ai_hub.backup.maintenance.dagster_cleanup_sql import execute_capped_delete


class LogLevelCleanupHandler(MaintenanceHandler):
    """Delete user-emitted Python log entries (``dagster_event_type IS NULL``) at a given level.

    Three handler instances are constructed by ``maintenance_handler_factory``,
    one per log level (DEBUG=10, INFO=20, WARNING=30). They differ only in
    the configured level (which becomes part of the WHERE clause) and the
    label used for logging + Dagster output metadata. ``ASSET_MATERIALIZATION``,
    ``STEP_SUCCESS`` and other framework events are not touched — those have
    a non-NULL ``dagster_event_type``.
    """

    def __init__(
        self,
        label: str,
        level: str,
        engine: Engine,
        delete_after_days: int,
        batch_limit: int,
    ) -> None:
        self._label = label
        self._level = level
        self._where = f"dagster_event_type IS NULL AND event::jsonb->>'level' = '{level}'"
        self._engine = engine
        self._delete_after_days = delete_after_days
        self._batch_limit = batch_limit

    @property
    @override
    def service_name(self) -> str:
        return self._label

    @override
    def run(self) -> MaintenanceResult:
        try:
            rows, duration = execute_capped_delete(
                self._engine, self._label, self._where, self._delete_after_days, self._batch_limit
            )
        except Exception as e:
            return MaintenanceResult(name=self._label, succeeded=False, error=str(e))
        return MaintenanceResult(
            name=self._label,
            succeeded=True,
            duration_seconds=round(duration, 1),
            rows_affected=rows,
            metadata={
                "retention_days": self._delete_after_days,
                "batch_limit": self._batch_limit,
                "level": self._level,
            },
        )
