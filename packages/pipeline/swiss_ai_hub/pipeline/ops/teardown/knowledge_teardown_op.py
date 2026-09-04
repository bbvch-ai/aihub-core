from dagster import Config, OpExecutionContext, op

from swiss_ai_hub.pipeline.services.knowledge_teardown_service import KnowledgeTeardownService
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.partition_utils import COMPOSITE_PARTITION_KEY_SEPARATOR


class KnowledgeTeardownConfig(Config):
    """Per-run parameters for a teardown, derived by the teardown sensor from the flagged entity rows.

    ``partition_registry_name`` is the ingestor-derived dynamic-partition registry name; it is supplied by
    the sensor (which knows the ingestor) rather than stored on the entity, so the API stays unaware of
    pipeline naming.
    """

    teardown_type: str
    bucket_id: str
    bucket_name: str
    db_name: str
    partition_registry_name: str
    namespace_id: str | None = None
    namespace_name: str | None = None
    folder_name: str | None = None


@op(description="Tears down a knowledge database or one namespace across Milvus, the doc store and S3.")
def knowledge_teardown_op(context: OpExecutionContext, config: KnowledgeTeardownConfig) -> None:
    """Adapter around ``KnowledgeTeardownService``; only the partition purge needs Dagster's instance."""
    ensure_main_db_connection()

    if config.teardown_type == "database":
        KnowledgeTeardownService.teardown_database(
            bucket_id=config.bucket_id, bucket_name=config.bucket_name, db_name=config.db_name
        )
        _purge_bucket_partitions(context, config.partition_registry_name, config.bucket_name)
    elif config.teardown_type == "namespace":
        KnowledgeTeardownService.teardown_namespace(
            namespace_id=config.namespace_id,
            namespace_name=config.namespace_name,
            folder_name=config.folder_name,
            bucket_name=config.bucket_name,
            db_name=config.db_name,
        )
    else:
        raise ValueError(f"Unknown teardown_type: {config.teardown_type}")


def _purge_bucket_partitions(context: OpExecutionContext, partition_registry_name: str, bucket_name: str) -> None:
    """Optional hygiene: drop the torn-down bucket's orphaned ``{bucket}|*`` composite partition keys.

    Not a correctness gate — re-ingestion of a re-uploaded file relies on the upload timestamp changing the
    DataVersion, not on partition state (Dagster OSS cannot wipe per-partition materialization memory anyway,
    issue #14749). But a deleted database's keys are never reconciled away otherwise (its bucket stops being
    enumerated), so they would bloat the shared registry forever. All matching keys are removed in one pass,
    deliberately bypassing the per-tick ``max_partitions`` cap that reconciliation uses.
    """
    prefix = f"{bucket_name}{COMPOSITE_PARTITION_KEY_SEPARATOR}"
    keys = [key for key in context.instance.get_dynamic_partitions(partition_registry_name) if key.startswith(prefix)]
    for key in keys:
        context.instance.delete_dynamic_partition(partitions_def_name=partition_registry_name, partition_key=key)
    if keys:
        context.log.info(f"Purged {len(keys)} orphaned partition keys for bucket '{bucket_name}'")
