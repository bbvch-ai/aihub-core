from datetime import UTC, datetime

from dagster import AssetExecutionContext, AssetKey, AssetsDefinition, ResourceParam, asset

from swiss_ai_hub.backup.container_discovery import ContainerDiscovery
from swiss_ai_hub.backup.dagster.types import BackupContext
from swiss_ai_hub.backup.models import TIMESTAMP_FORMAT


def backup_session_factory(key: AssetKey) -> AssetsDefinition:
    @asset(key=key, group_name="backup", description="Initialize backup run and stop all managed containers")
    def backup_session(
        context: AssetExecutionContext,
        container_discovery: ResourceParam[ContainerDiscovery],
    ) -> BackupContext:
        timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)

        context.log.info("Backup session: timestamp=%s", timestamp)

        previously_running = container_discovery.stop_all_managed()

        context.add_output_metadata(
            {"timestamp": timestamp, "s3_prefix": timestamp, "containers_stopped": len(previously_running)},
        )

        return BackupContext(timestamp=timestamp, s3_prefix=timestamp, previously_running=previously_running)

    return backup_session
