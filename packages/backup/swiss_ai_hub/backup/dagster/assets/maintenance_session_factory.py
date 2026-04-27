from datetime import UTC, datetime

from dagster import AssetExecutionContext, AssetKey, AssetsDefinition, asset

from swiss_ai_hub.backup.dagster.types import MaintenanceContext
from swiss_ai_hub.backup.models import TIMESTAMP_FORMAT


def maintenance_session_factory(key: AssetKey) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="maintenance",
        description="Initialize a maintenance run. Online-safe — does NOT stop any containers.",
    )
    def maintenance_session(context: AssetExecutionContext) -> MaintenanceContext:
        timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
        context.log.info("Maintenance session timestamp=%s run_id=%s", timestamp, context.run.run_id)
        context.add_output_metadata({"timestamp": timestamp, "run_id": context.run.run_id})
        return MaintenanceContext(timestamp=timestamp, run_id=context.run.run_id)

    return maintenance_session
