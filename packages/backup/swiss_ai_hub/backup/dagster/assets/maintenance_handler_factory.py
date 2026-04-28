from sqlalchemy import Engine

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler
from swiss_ai_hub.backup.maintenance.dagster_unimportant_events import DagsterUnimportantEventsHandler
from swiss_ai_hub.backup.maintenance.log_level_cleanup_handler import LogLevelCleanupHandler
from swiss_ai_hub.backup.maintenance.postgres_autovacuum_tune import PostgresAutovacuumTuneHandler
from swiss_ai_hub.backup.maintenance.postgres_indexes import PostgresIndexesHandler
from swiss_ai_hub.backup.maintenance.postgres_repack import PostgresRepackHandler
from swiss_ai_hub.backup.settings import BackupSettings

# Service names match the asset key suffixes used in maintenance_definitions().
# Order is irrelevant — assets define their own dependencies via ins=.
CLEANUP_HANDLER_NAMES: tuple[str, ...] = (
    "postgres_indexes",
    "postgres_autovacuum_tune",
    "dagster_debug_logs",
    "dagster_info_logs",
    "dagster_warning_logs",
    "dagster_unimportant_events",
)
REPACK_HANDLER_NAMES: tuple[str, ...] = ("postgres_repack",)

# Three of the cleanup handlers differ only in log level + retention window.
# Keep that knowledge here rather than scattering it across three near-identical
# handler files.
_LOG_LEVEL_HANDLERS: dict[str, tuple[str, str]] = {
    "dagster_debug_logs": ("10", "DAGSTER_DEBUG_LOG_RETENTION_DAYS"),
    "dagster_info_logs": ("20", "DAGSTER_INFO_LOG_RETENTION_DAYS"),
    "dagster_warning_logs": ("30", "DAGSTER_WARNING_LOG_RETENTION_DAYS"),
}


def create_maintenance_handler(
    service_name: str,
    settings: BackupSettings,
    engine: Engine,
) -> MaintenanceHandler:
    """Construct a maintenance handler by name."""
    if service_name == "postgres_indexes":
        return PostgresIndexesHandler(engine)
    if service_name == "postgres_autovacuum_tune":
        return PostgresAutovacuumTuneHandler(engine)
    if service_name in _LOG_LEVEL_HANDLERS:
        level, retention_attr = _LOG_LEVEL_HANDLERS[service_name]
        return LogLevelCleanupHandler(
            label=service_name,
            level=level,
            engine=engine,
            delete_after_days=getattr(settings, retention_attr),
            batch_limit=settings.DAGSTER_CLEANUP_BATCH_LIMIT,
        )
    if service_name == "dagster_unimportant_events":
        return DagsterUnimportantEventsHandler(
            engine, settings.DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS, settings.DAGSTER_CLEANUP_BATCH_LIMIT
        )
    if service_name == "postgres_repack":
        return PostgresRepackHandler(settings)
    raise ValueError(f"Unknown maintenance service: {service_name}")
