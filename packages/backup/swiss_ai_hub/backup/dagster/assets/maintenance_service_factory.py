from dagster import AssetExecutionContext, AssetIn, AssetKey, AssetsDefinition, ResourceParam, asset
from sqlalchemy import Engine

from swiss_ai_hub.backup.dagster.assets.maintenance_handler_factory import create_maintenance_handler
from swiss_ai_hub.backup.dagster.types import MaintenanceContext
from swiss_ai_hub.backup.maintenance.base import MaintenanceResult
from swiss_ai_hub.backup.settings import BackupSettings


def maintenance_service_factory(
    key: AssetKey,
    session_key: AssetKey,
    service_name: str,
    description: str,
) -> AssetsDefinition:
    """Per-handler asset. Failures are returned as MaintenanceResult, NOT raised.

    This isolates each handler — one failed cleanup does not stop the others.
    The finalize asset aggregates results and decides whether to mark the run
    as failed.
    """

    @asset(
        key=key,
        group_name="maintenance",
        ins={"session": AssetIn(key=session_key)},
        description=description,
    )
    def maintenance_service(
        context: AssetExecutionContext,
        session: MaintenanceContext,
        backup_settings: ResourceParam[BackupSettings],
        maintenance_engine: ResourceParam[Engine],
    ) -> MaintenanceResult:
        if backup_settings.MAINTENANCE_DISABLED:
            context.log.info("Maintenance disabled via MAINTENANCE_DISABLED — skipping %s", service_name)
            return MaintenanceResult(name=service_name, succeeded=True, metadata={"skipped": "MAINTENANCE_DISABLED"})

        handler = create_maintenance_handler(service_name, backup_settings, maintenance_engine)
        context.log.info("Running maintenance handler: %s", service_name)
        result = handler.run()

        metadata: dict[str, str | int | float] = {
            "succeeded": str(result.succeeded),
            "duration_seconds": result.duration_seconds,
        }
        if result.rows_affected is not None:
            metadata["rows_affected"] = result.rows_affected
        if result.error:
            metadata["error"] = result.error[:500]
        metadata.update(result.metadata)
        context.add_output_metadata(metadata)

        if result.succeeded:
            context.log.info(
                "[%s] OK rows=%s duration=%.1fs", service_name, result.rows_affected, result.duration_seconds
            )
        else:
            context.log.error("[%s] FAILED: %s", service_name, result.error)
        return result

    return maintenance_service
