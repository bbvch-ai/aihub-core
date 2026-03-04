import logging
import time

from dagster import AssetExecutionContext, AssetIn, AssetKey, AssetsDefinition, ResourceParam, asset

from aihub_backup.container_lifecycle import SERVICE_DEPS, ContainerLifecycleManager
from aihub_backup.dagster.assets.handler_factory import create_handler
from aihub_backup.dagster.ops.types import BackupContext
from aihub_backup.docker_client import DockerManager
from aihub_backup.models import ServiceResult, ServiceStatus
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)


def backup_service_factory(
    key: AssetKey,
    session_key: AssetKey,
    service_name: str,
    description: str,
) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="backup",
        ins={"session": AssetIn(key=session_key)},
        description=description,
    )
    def service_backup(
        context: AssetExecutionContext,
        session: BackupContext,
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
            result = _run_backup(context, handler, session)
        finally:
            if deps.containers:
                container_lifecycle.stop_containers(service_name, deps.containers)

        context.add_output_metadata(
            {
                "status": result.status.value,
                "duration_seconds": result.duration_seconds,
                "s3_prefix": f"s3://{s3_manager.bucket}/{session.s3_prefix}/",
            },
        )
        return result

    return service_backup


def _run_backup(
    context: AssetExecutionContext,
    handler: BackupHandler,
    session: BackupContext,
) -> ServiceResult:
    context.log.info("Backing up: %s", handler.service_name)
    start = time.monotonic()
    try:
        handler.backup(session.timestamp, session.s3_prefix)
        duration = time.monotonic() - start
        context.log.info("%s completed in %.0fs", handler.service_name, duration)
        return ServiceResult(
            name=handler.service_name,
            status=ServiceStatus.SUCCEEDED,
            duration_seconds=round(duration, 1),
        )
    except Exception as e:
        duration = time.monotonic() - start
        context.log.error("%s FAILED after %.0fs: %s", handler.service_name, duration, e)
        return ServiceResult(
            name=handler.service_name,
            status=ServiceStatus.FAILED,
            duration_seconds=round(duration, 1),
            error=str(e),
        )
