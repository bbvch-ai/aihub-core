import dagster as dg

from aihub_backup.dagster.config import RestoreConfig, SingleServiceRestoreConfig
from aihub_backup.dagster.resources import (
    BackupHandlersResource,
    BackupSettingsResource,
    DockerManagerResource,
    S3ManagerResource,
    build_orchestrator,
)
from aihub_backup.models import ServiceResult, ServiceStatus


@dg.op
def run_full_restore(
    context: dg.OpExecutionContext,
    config: RestoreConfig,
    backup_settings: BackupSettingsResource,
    s3_manager: S3ManagerResource,
    docker_manager: DockerManagerResource,
    backup_handlers: BackupHandlersResource,
) -> None:
    orchestrator, _ = build_orchestrator(backup_settings, s3_manager, docker_manager, backup_handlers)

    def on_service_complete(result: ServiceResult) -> None:
        context.log.info("Service restored: %s", result)

    summary = orchestrator.run_restore(
        timestamp=config.timestamp, on_service_complete=on_service_complete, force=config.force
    )

    failed = [r for r in summary.results if r.status == ServiceStatus.FAILED]
    if failed:
        raise dg.Failure(
            description=f"Restore failed for: {', '.join(r.name for r in failed)}",
            metadata={
                "failed_services": dg.MetadataValue.text(", ".join(r.name for r in failed)),
                "duration_seconds": dg.MetadataValue.float(summary.total_duration_seconds),
            },
        )

    context.log.info("Full restore completed in %.0fs", summary.total_duration_seconds)


@dg.op
def run_single_service_restore(
    context: dg.OpExecutionContext,
    config: SingleServiceRestoreConfig,
    backup_settings: BackupSettingsResource,
    s3_manager: S3ManagerResource,
    docker_manager: DockerManagerResource,
    backup_handlers: BackupHandlersResource,
) -> None:
    orchestrator, _ = build_orchestrator(backup_settings, s3_manager, docker_manager, backup_handlers)

    result = orchestrator.run_single_restore(service_name=config.service_name, timestamp=config.timestamp)

    if result.status == ServiceStatus.FAILED:
        raise dg.Failure(
            description=f"{config.service_name} restore failed: {result.error}",
            metadata={
                "service": dg.MetadataValue.text(config.service_name),
                "error": dg.MetadataValue.text(result.error or "unknown"),
                "duration_seconds": dg.MetadataValue.float(result.duration_seconds),
            },
        )

    context.log.info(
        "%s restore completed in %.0fs",
        config.service_name,
        result.duration_seconds,
    )
