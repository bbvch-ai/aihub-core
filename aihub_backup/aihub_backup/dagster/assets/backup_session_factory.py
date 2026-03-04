from datetime import UTC, datetime

from dagster import AssetExecutionContext, AssetKey, AssetsDefinition, ResourceParam, asset

from aihub_backup.container_discovery import ContainerDiscovery
from aihub_backup.dagster.ops.types import BackupContext
from aihub_backup.models import TIMESTAMP_FORMAT
from aihub_backup.s3 import S3Manager


def backup_session_factory(key: AssetKey) -> AssetsDefinition:
    @asset(key=key, group_name="backup", description="Initialize backup run")
    def backup_session(
        context: AssetExecutionContext,
        s3_manager: ResourceParam[S3Manager],
        container_discovery: ResourceParam[ContainerDiscovery],
    ) -> BackupContext:
        timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
        prefix = timestamp

        existing = s3_manager.count_objects(prefix + "/")
        if existing > 0:
            context.log.warning("Purging %d objects from previous attempt at %s/", existing, prefix)
            s3_manager.delete_recursive(prefix + "/")

        context.log.info(
            "Backup session: timestamp=%s, dest=s3://%s/%s/",
            timestamp,
            s3_manager.bucket,
            prefix,
        )

        previously_running = container_discovery.stop_all_managed()

        context.add_output_metadata(
            {"timestamp": timestamp, "s3_prefix": prefix, "containers_stopped": len(previously_running)},
        )

        return BackupContext(timestamp=timestamp, s3_prefix=prefix, previously_running=previously_running)

    return backup_session
