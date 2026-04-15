from dagster import AssetExecutionContext, AssetIn, AssetKey, AssetsDefinition, Failure, ResourceParam, asset

from swiss_ai_hub.backup.container_discovery import ContainerDiscovery
from swiss_ai_hub.backup.dagster.partitions import backup_partitions
from swiss_ai_hub.backup.dagster.types import BackupContext
from swiss_ai_hub.backup.models import ServiceResult, ServiceStatus
from swiss_ai_hub.backup.retention import RetentionService
from swiss_ai_hub.backup.s3 import BACKUP_PREFIX_RE, S3Manager
from swiss_ai_hub.backup.settings import BackupSettings


def backup_finalize_factory(
    key: AssetKey,
    session_key: AssetKey,
    service_keys: dict[str, AssetKey],
) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="backup",
        ins={
            "session": AssetIn(key=session_key),
            **{name: AssetIn(key=ak) for name, ak in service_keys.items()},
        },
        description="Restart services and run retention cleanup",
    )
    def backup_finalize(
        context: AssetExecutionContext,
        session: BackupContext,
        container_discovery: ResourceParam[ContainerDiscovery],
        backup_settings: ResourceParam[BackupSettings],
        s3_manager: ResourceParam[S3Manager],
        **service_results: ServiceResult,
    ) -> list[ServiceResult]:
        container_discovery.start_all(session.previously_running)

        try:
            RetentionService.run(s3_manager, backup_settings.BACKUP_RETENTION_DAYS, backup_settings.BACKUP_MINIMUM_KEEP)
        except Exception as e:
            context.log.warning("Retention cleanup failed: %s", e)

        _sync_partitions(context, s3_manager)

        results = list(service_results.values())
        failed = [r for r in results if r.status == ServiceStatus.FAILED]

        context.add_output_metadata(
            {
                "total_services": len(results),
                "succeeded": len([r for r in results if r.status == ServiceStatus.SUCCEEDED]),
                "failed": len(failed),
                "skipped": len([r for r in results if r.status == ServiceStatus.SKIPPED]),
                "containers_restarted": len(session.previously_running),
            },
        )

        if failed:
            failed_names = ", ".join(r.name for r in failed)
            raise Failure(
                description=f"Backup failed for: {failed_names}",
                metadata={"failed_services": failed_names},
            )

        return results

    return backup_finalize


def _sync_partitions(context: AssetExecutionContext, s3: S3Manager) -> None:
    """Sync S3 backup prefixes to dynamic partitions for the restore job selector."""
    s3_prefixes = {p for p in s3.list_prefixes() if BACKUP_PREFIX_RE.match(p)}
    existing = set(context.instance.get_dynamic_partitions(backup_partitions.name))

    to_add = list(s3_prefixes - existing)
    to_remove = list(existing - s3_prefixes)

    if to_add:
        context.instance.add_dynamic_partitions(
            partitions_def_name=backup_partitions.name,
            partition_keys=to_add,
        )
        context.log.info("Added %d backup partition(s): %s", len(to_add), ", ".join(sorted(to_add)))

    for key in to_remove:
        context.instance.delete_dynamic_partition(
            partitions_def_name=backup_partitions.name,
            partition_key=key,
        )
    if to_remove:
        context.log.info("Removed %d stale partition(s): %s", len(to_remove), ", ".join(sorted(to_remove)))
