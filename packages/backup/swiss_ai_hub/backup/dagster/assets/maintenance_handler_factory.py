from sqlalchemy import Engine

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler
from swiss_ai_hub.backup.maintenance.dagster_debug_logs import DagsterDebugLogsHandler
from swiss_ai_hub.backup.maintenance.dagster_info_logs import DagsterInfoLogsHandler
from swiss_ai_hub.backup.maintenance.dagster_unimportant_events import DagsterUnimportantEventsHandler
from swiss_ai_hub.backup.maintenance.dagster_warning_logs import DagsterWarningLogsHandler
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
    if service_name == "dagster_debug_logs":
        return DagsterDebugLogsHandler(
            engine, settings.MAINTENANCE_DEBUG_LOG_RETENTION_DAYS, settings.MAINTENANCE_BATCH_LIMIT
        )
    if service_name == "dagster_info_logs":
        return DagsterInfoLogsHandler(
            engine, settings.MAINTENANCE_INFO_LOG_RETENTION_DAYS, settings.MAINTENANCE_BATCH_LIMIT
        )
    if service_name == "dagster_warning_logs":
        return DagsterWarningLogsHandler(
            engine, settings.MAINTENANCE_WARNING_LOG_RETENTION_DAYS, settings.MAINTENANCE_BATCH_LIMIT
        )
    if service_name == "dagster_unimportant_events":
        return DagsterUnimportantEventsHandler(
            engine, settings.MAINTENANCE_UNIMPORTANT_EVENT_RETENTION_DAYS, settings.MAINTENANCE_BATCH_LIMIT
        )
    if service_name == "postgres_repack":
        return PostgresRepackHandler(settings)
    raise ValueError(f"Unknown maintenance service: {service_name}")
