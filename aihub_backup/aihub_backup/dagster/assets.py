from collections.abc import Iterator

import dagster as dg

from aihub_backup.dagster.config import BackupConfig
from aihub_backup.dagster.resources import (
    BackupHandlersResource,
    BackupSettingsResource,
    DockerManagerResource,
    S3ManagerResource,
    build_orchestrator,
)
from aihub_backup.models import SERVICE_TO_ASSET_KEY, BackupMode, ServiceResult, ServiceStatus

daily_partitions = dg.DailyPartitionsDefinition(
    start_date="2026-01-01",
    end_offset=1,
    timezone="Europe/Zurich",
)


@dg.multi_asset(
    outs={
        "postgres_backup": dg.AssetOut(group_name="backup", description="PostgreSQL database dumps"),
        "milvus_backup": dg.AssetOut(group_name="backup", description="Milvus vector database backup"),
        "neo4j_backup": dg.AssetOut(group_name="backup", description="Neo4j graph database dump"),
        "clickhouse_backup": dg.AssetOut(group_name="backup", description="ClickHouse database backup"),
        "valkey_backup": dg.AssetOut(group_name="backup", description="Valkey (Redis) RDB snapshot"),
        "nats_backup": dg.AssetOut(group_name="backup", description="NATS JetStream streams backup"),
    },
    partitions_def=daily_partitions,
    can_subset=False,
    retry_policy=dg.RetryPolicy(max_retries=2, delay=60),
)
def create_backup(
    context: dg.AssetExecutionContext,
    config: BackupConfig,
    backup_settings: BackupSettingsResource,
    s3_manager: S3ManagerResource,
    docker_manager: DockerManagerResource,
    backup_handlers: BackupHandlersResource,
) -> Iterator[dg.MaterializeResult]:
    orchestrator, s3 = build_orchestrator(backup_settings, s3_manager, docker_manager, backup_handlers)
    mode = BackupMode(config.mode)

    def on_service_complete(result: ServiceResult) -> None:
        context.log.info("Service completed: %s", result)

    summary = orchestrator.run_backup(mode=mode, on_service_complete=on_service_complete)

    for result in summary.results:
        asset_key = SERVICE_TO_ASSET_KEY[result.name]
        metadata: dict[str, dg.MetadataValue] = {
            "status": dg.MetadataValue.text(result.status.value),
            "duration_seconds": dg.MetadataValue.float(result.duration_seconds),
            "timestamp": dg.MetadataValue.text(summary.timestamp),
            "mode": dg.MetadataValue.text(summary.mode.value),
            "s3_prefix": dg.MetadataValue.text(f"s3://{s3.bucket}/{summary.timestamp}_{summary.mode.value}/"),
            "partition_key": dg.MetadataValue.text(context.partition_key),
        }
        if summary.retention_warning:
            metadata["retention_warning"] = dg.MetadataValue.text(summary.retention_warning)
        yield dg.MaterializeResult(asset_key=asset_key, metadata=metadata)

    # Yield MaterializeResult entries first so Dagster records individual asset
    # outcomes, then raise Failure to mark the overall run as failed.
    failed = [r for r in summary.results if r.status == ServiceStatus.FAILED]
    if failed:
        raise dg.Failure(description=f"{len(failed)} service(s) failed: {', '.join(r.name for r in failed)}")
