import logging
import time

from dagster import AssetExecutionContext, AssetIn, AssetKey, AssetsDefinition, ResourceParam, asset

from aihub_backup.container_lifecycle import SERVICE_DEPS, ContainerLifecycleManager
from aihub_backup.dagster.assets.handler_factory import create_handler
from aihub_backup.dagster.ops.types import RestoreContext
from aihub_backup.dagster.partitions import backup_partitions
from aihub_backup.docker_client import DockerManager
from aihub_backup.models import ServiceResult, ServiceStatus
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)


def restore_service_factory(
    key: AssetKey,
    session_key: AssetKey,
    service_name: str,
    description: str,
) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="restore",
        partitions_def=backup_partitions,
        ins={"session": AssetIn(key=session_key)},
        description=description,
    )
    def service_restore(
        context: AssetExecutionContext,
        session: RestoreContext,
        backup_settings: ResourceParam[BackupSettings],
        s3_manager: ResourceParam[S3Manager],
        docker_manager: ResourceParam[DockerManager],
        container_lifecycle: ResourceParam[ContainerLifecycleManager],
    ) -> ServiceResult:
        deps = SERVICE_DEPS[service_name]

        if deps.containers:
            context.log.info("Starting %s dependencies: %s", service_name, ", ".join(deps.containers))
            container_lifecycle.start_and_await_healthy(deps.containers, timeout=deps.timeout, label=service_name)

        try:
            handler = create_handler(service_name, backup_settings, s3_manager, docker_manager)
            result = _run_restore(context, handler, session.timestamp)
        finally:
            if deps.containers:
                container_lifecycle.stop_containers(service_name, deps.containers)

        context.add_output_metadata(
            {
                "status": result.status.value,
                "duration_seconds": result.duration_seconds,
            },
        )
        return result

    return service_restore


def _run_restore(
    context: AssetExecutionContext,
    handler: BackupHandler,
    timestamp: str,
) -> ServiceResult:
    """Run a single restore — failures propagate to crash the asset.

    Unlike backup (which catches errors so other services can continue),
    restore lets exceptions propagate so the Dagster run fails immediately.
    A partially restored system is dangerous — a human must investigate.
    """
    context.log.info("Restoring: %s", handler.service_name)
    start = time.monotonic()
    handler.restore(timestamp)
    duration = time.monotonic() - start
    context.log.info("%s completed in %.0fs", handler.service_name, duration)
    return ServiceResult(
        name=handler.service_name,
        status=ServiceStatus.SUCCEEDED,
        duration_seconds=round(duration, 1),
    )
