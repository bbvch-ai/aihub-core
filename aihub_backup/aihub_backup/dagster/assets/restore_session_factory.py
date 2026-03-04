import logging

from dagster import AssetExecutionContext, AssetKey, AssetsDefinition, ResourceParam, asset

from aihub_backup.container_discovery import ContainerDiscovery
from aihub_backup.dagster.ops.types import RestoreContext
from aihub_backup.dagster.partitions import backup_partitions
from aihub_backup.s3 import S3Manager

logger = logging.getLogger(__name__)


def restore_session_factory(key: AssetKey) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="restore",
        partitions_def=backup_partitions,
        description="Validate backup and stop all services",
    )
    def restore_session(
        context: AssetExecutionContext,
        s3_manager: ResourceParam[S3Manager],
        container_discovery: ResourceParam[ContainerDiscovery],
    ) -> RestoreContext:
        timestamp: str = context.partition_key
        resolved = s3_manager.resolve_timestamp(timestamp)
        logger.info("Resolved timestamp: %s -> %s", timestamp, resolved)

        context.log.info("=== Phase 1: Validation ===")
        _validate_backup_completeness_or_raise(s3_manager, resolved, context)

        context.log.info("=== Phase 2: Stopping all services ===")
        container_discovery.stop_all_managed()

        context.add_output_metadata({"timestamp": resolved})

        return RestoreContext(timestamp=resolved)

    return restore_session


def _validate_backup_completeness_or_raise(
    s3: S3Manager,
    timestamp: str,
    context: AssetExecutionContext,
) -> None:
    missing: list[str] = []

    if not s3.file_exists(f"{timestamp}/postgres-main/globals.sql.gz"):
        missing.append("PostgreSQL (main)")
    if not s3.file_exists(f"{timestamp}/postgres-ferretdb/globals.sql.gz"):
        missing.append("PostgreSQL (FerretDB)")
    if not s3.file_exists(f"{timestamp}/neo4j.dump"):
        missing.append("Neo4j")
    ch_prefixes = s3.list_prefixes(f"{timestamp}/clickhouse/")
    if not ch_prefixes:
        missing.append("ClickHouse")
    if not s3.file_exists(f"{timestamp}/valkey.rdb"):
        missing.append("Valkey")
    if not s3.file_exists(f"{timestamp}/nats-jetstream.tar.gz"):
        missing.append("NATS JetStream")

    milvus_prefixes = s3.list_prefixes(f"{timestamp}/")
    if not any("milvus_backup_" in p for p in milvus_prefixes):
        missing.append("Milvus")

    if missing:
        raise RuntimeError(f"Missing backups: {', '.join(missing)}")

    context.log.info("All backups validated")
