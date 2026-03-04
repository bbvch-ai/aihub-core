from __future__ import annotations

from typing import TYPE_CHECKING

from dagster import AssetsDefinition, HookContext, define_asset_job, failure_hook

if TYPE_CHECKING:
    from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

from aihub_backup.container_discovery import ContainerDiscovery
from aihub_backup.dagster.partitions import backup_partitions


@failure_hook
def restart_on_failure(context: HookContext) -> None:
    """Restart all services if session asset fails after stopping containers.

    Restarts all managed containers (not just previously_running) because if the
    session asset crashes after stopping containers, the previously_running list
    is lost. Safety-first: over-starting is harmless, leaving services down is not.
    """
    discovery = ContainerDiscovery()
    all_managed = discovery.discover_managed_containers()
    discovery.start_all(all_managed)


def backup_asset_job(assets: list[AssetsDefinition]) -> UnresolvedAssetJobDefinition:
    return define_asset_job(
        name="backup_asset_job",
        selection=assets,
        description="Run a full system backup (all services).",
        hooks={restart_on_failure},
    )


def restore_asset_job(assets: list[AssetsDefinition]) -> UnresolvedAssetJobDefinition:
    return define_asset_job(
        name="full_restore_job",
        selection=assets,
        partitions_def=backup_partitions,
        description="Restore all services from a backup. Select a partition to choose timestamp. "
        "On success, containers are restarted. On failure, containers stay stopped — human must investigate.",
    )
