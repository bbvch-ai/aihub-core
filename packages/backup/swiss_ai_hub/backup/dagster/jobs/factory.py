from __future__ import annotations

from typing import TYPE_CHECKING

from dagster import AssetsDefinition, HookContext, define_asset_job, failure_hook

if TYPE_CHECKING:
    from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

from swiss_ai_hub.backup.container_discovery import ContainerDiscovery


@failure_hook
def restart_on_failure(context: HookContext) -> None:
    """Restart all services if session asset fails after stopping containers.

    Restarts all managed containers (not just previously_running) because if the
    session asset crashes after stopping containers, the previously_running list
    is lost. Safety-first: over-starting is harmless, leaving services down is not.
    """
    context.log.warning("Backup failed — restarting all managed containers as safety measure")
    try:
        discovery = ContainerDiscovery()
        all_managed = discovery.discover_managed_containers()
        discovery.start_all(all_managed)
        context.log.info("All containers restarted after failure recovery")
    except Exception:
        context.log.error(
            "Failed to restart containers during failure recovery — manual intervention required",
            exc_info=True,
        )


def backup_asset_job(assets: list[AssetsDefinition]) -> UnresolvedAssetJobDefinition:
    return define_asset_job(
        name="backup_asset_job",
        selection=assets,
        description="Run a full system backup (stop and restart all services).",
        hooks={restart_on_failure},
    )
