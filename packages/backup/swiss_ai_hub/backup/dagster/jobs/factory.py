from __future__ import annotations

from typing import TYPE_CHECKING

from dagster import AssetsDefinition, HookContext, define_asset_job, failure_hook

if TYPE_CHECKING:
    from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

from swiss_ai_hub.backup.container_discovery import ContainerDiscovery
from swiss_ai_hub.backup.dagster.partitions import backup_partitions

# Mutex tag — every job that touches Postgres or stops postgres carries this so
# the QueuedRunCoordinator serializes them. Other future jobs (sensors,
# health checks, ad-hoc utilities) without this tag run unimpeded in parallel.
# Configured in infra/deployment/templates/configs/backup-dagster.yml.j2 under
# run_coordinator.tag_concurrency_limits.
POSTGRES_MUTEX_TAG = {"postgres-mutex": "true"}


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
        tags=POSTGRES_MUTEX_TAG,
    )


def restore_asset_job(assets: list[AssetsDefinition]) -> UnresolvedAssetJobDefinition:
    return define_asset_job(
        name="full_restore_job",
        selection=assets,
        partitions_def=backup_partitions,
        description="Restore all services from a backup. Select a partition to choose timestamp. "
        "On success, containers are restarted. On failure, containers stay stopped — human must investigate.",
        tags=POSTGRES_MUTEX_TAG,
    )


def cleanup_asset_job(assets: list[AssetsDefinition]) -> UnresolvedAssetJobDefinition:
    return define_asset_job(
        name="dagster_cleanup_job",
        selection=assets,
        description=(
            "Online-safe Postgres maintenance for the dagster DB: prune verbose Python logs and "
            "transient framework events from event_logs, ensure cleanup indexes exist, apply "
            "autovacuum tuning. UI-safe by construction — never touches ASSET_MATERIALIZATION, "
            "STEP_SUCCESS, or STEP_FAILURE events."
        ),
        tags=POSTGRES_MUTEX_TAG,
    )


def repack_asset_job(assets: list[AssetsDefinition]) -> UnresolvedAssetJobDefinition:
    return define_asset_job(
        name="postgres_repack_job",
        selection=assets,
        description=(
            "Run pg_repack on the heavy Dagster tables to return disk space to the OS. "
            "VACUUM alone marks dead rows reusable internally but does not free disk pages."
        ),
        tags=POSTGRES_MUTEX_TAG,
    )
