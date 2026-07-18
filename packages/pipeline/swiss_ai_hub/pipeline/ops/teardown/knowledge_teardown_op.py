import mongoengine
from dagster import Config, OpExecutionContext, op
from mongoengine import register_connection
from swiss_ai_hub.core.infrastructure import MongoSettings
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity, RefDoc

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.partition_utils import COMPOSITE_PARTITION_KEY_SEPARATOR
from swiss_ai_hub.pipeline.util.store_builders import build_s3_file_access_service, build_vector_store


class KnowledgeTeardownConfig(Config):
    """Per-run parameters for a teardown, populated by the teardown sensor from the teardown event.

    ``partition_registry_name`` is the ingestor-derived dynamic-partition registry name; it is supplied by
    the sensor (which knows the ingestor) rather than the event, so the API stays unaware of pipeline naming.
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
    """Perform the destructive multi-store teardown, then hard-delete the entity rows as the final step.

    Every step is idempotent, so a failed run is safe to retry ("retry until clean") rather than leaving a
    silent half-deletion. The entity rows survive (flagged ``deleting``, excluded from enumeration) until
    this op removes them, which is what lets the sensor keep finding the event's bucket to route the run.
    """
    ensure_main_db_connection()
    _dispatch_teardown(context, config)


def _dispatch_teardown(context: OpExecutionContext, config: KnowledgeTeardownConfig) -> None:
    if config.teardown_type == "database":
        _teardown_database(context, config)
    elif config.teardown_type == "namespace":
        _teardown_namespace(context, config)
    else:
        raise ValueError(f"Unknown teardown_type: {config.teardown_type}")


def _teardown_database(context: OpExecutionContext, config: KnowledgeTeardownConfig) -> None:
    context.log.info(f"Tearing down knowledge database '{config.db_name}' (bucket '{config.bucket_name}')")

    build_vector_store(config.db_name).drop_collection()

    _ensure_docstore_alias(config.db_name)
    RefDoc.drop_database(config.db_name)

    build_s3_file_access_service().delete_container(config.bucket_name)

    _purge_bucket_partitions(context, config.partition_registry_name, config.bucket_name)

    NamespaceEntity.delete_all_for_bucket(config.bucket_id)
    BucketEntity.delete_bucket(config.bucket_id)

    context.log.info(f"Teardown complete for database '{config.db_name}'")


def _teardown_namespace(context: OpExecutionContext, config: KnowledgeTeardownConfig) -> None:
    context.log.info(f"Tearing down namespace '{config.namespace_name}' in database '{config.db_name}'")

    build_s3_file_access_service().delete_prefix(config.bucket_name, f"{config.folder_name}/")

    _ensure_docstore_alias(config.db_name)
    RefDoc.delete_by_namespace(config.db_name, config.namespace_name)

    # Filtered delete, never a partition drop: namespaces share hashed Milvus partitions, so dropping the
    # partition would also wipe any colliding namespace's vectors.
    build_vector_store(config.db_name).delete_by_namespace(config.namespace_name)

    NamespaceEntity.delete_namespace(config.namespace_id)

    context.log.info(f"Teardown complete for namespace '{config.namespace_name}'")


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


def _ensure_docstore_alias(db_name: str) -> None:
    """Register the per-database mongoengine alias that RefDoc.drop_database / delete_by_namespace switch to.

    The doc store lives in its own Mongo database named after ``db_name``; only the ``default`` alias is
    registered by the pipeline, so the per-database alias must be added before the RefDoc teardown calls.
    """
    try:
        mongoengine.connection.get_connection(alias=db_name)
    except Exception:
        register_connection(
            alias=db_name,
            name=db_name,
            host=MongoSettings().CONNECTION_STRING.get_secret_value(),
            uuidRepresentation="standard",
        )
