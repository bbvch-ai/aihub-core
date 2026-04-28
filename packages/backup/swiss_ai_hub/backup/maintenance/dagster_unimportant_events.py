from typing import override

from sqlalchemy import Engine

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult
from swiss_ai_hub.backup.maintenance.dagster_cleanup_sql import execute_capped_delete

_LABEL = "dagster_unimportant_events"

# Curated list from docs.dagster.io/deployment/troubleshooting/database-tuning.
# These are framework-internal transient events, not user-visible state. UI
# does not depend on them after the run completes.
# IMPORTANT: ASSET_MATERIALIZATION, STEP_SUCCESS, STEP_FAILURE are NOT here —
# the asset catalog and run detail pages depend on those.
_UNIMPORTANT_EVENT_TYPES = (
    "ASSET_MATERIALIZATION_PLANNED",
    "ENGINE_EVENT",
    "HANDLED_OUTPUT",
    "LOADED_INPUT",
    "STEP_OUTPUT",
)
_WHERE = f"dagster_event_type IN ({', '.join(repr(t) for t in _UNIMPORTANT_EVENT_TYPES)})"


class DagsterUnimportantEventsHandler(MaintenanceHandler):
    """Delete framework-internal transient event types older than the configured retention.

    Targets the noisy bulk: HANDLED_OUTPUT and LOADED_INPUT alone are emitted
    for every op output/input edge in every run. On a deployment with 287K
    runs, these events dominate the event_logs table. The asset catalog
    queries ``ASSET_MATERIALIZATION`` events, which are deliberately excluded
    from this cleanup.
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
            metadata={
                "retention_days": self._delete_after_days,
                "batch_limit": self._batch_limit,
                "event_types": ", ".join(_UNIMPORTANT_EVENT_TYPES),
            },
        )
