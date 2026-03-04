from dagster import AssetExecutionContext, AssetIn, AssetKey, AssetsDefinition, ResourceParam, asset

from aihub_backup.container_discovery import ContainerDiscovery
from aihub_backup.dagster.ops.types import RestoreContext
from aihub_backup.dagster.partitions import backup_partitions
from aihub_backup.models import ServiceResult, ServiceStatus


def restore_finalize_factory(
    key: AssetKey,
    session_key: AssetKey,
    service_keys: dict[str, AssetKey],
) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="restore",
        partitions_def=backup_partitions,
        ins={
            "session": AssetIn(key=session_key),
            **{name: AssetIn(key=ak) for name, ak in service_keys.items()},
        },
        description="Restart all services after successful restore. Only runs if every service restored successfully.",
    )
    def restore_finalize(
        context: AssetExecutionContext,
        session: RestoreContext,
        container_discovery: ResourceParam[ContainerDiscovery],
        **service_results: ServiceResult,
    ) -> list[ServiceResult]:
        results = list(service_results.values())

        context.log.info("All restores succeeded — restarting services")
        all_managed = container_discovery.discover_managed_containers()
        container_discovery.start_all(all_managed)

        context.add_output_metadata(
            {
                "total_services": len(results),
                "succeeded": len([r for r in results if r.status == ServiceStatus.SUCCEEDED]),
                "containers_restarted": len(all_managed),
            },
        )

        context.log.info("Full restore completed successfully")
        return results

    return restore_finalize
