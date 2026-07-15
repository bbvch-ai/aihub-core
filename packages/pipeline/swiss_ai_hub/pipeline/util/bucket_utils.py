import mongoengine
from mongoengine import DoesNotExist, register_connection
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities import BucketEntity, NamespaceEntity

# Default alias for the main database connection
_DB_ALIAS = "default"


def _ensure_connection() -> None:
    """Ensure MongoDB connection is registered. Safe to call multiple times."""
    try:
        mongoengine.connection.get_connection(alias=_DB_ALIAS)
    except Exception:
        register_connection(
            alias=_DB_ALIAS,
            name=AIHubSettings().MONGO_MAIN_DB_NAME,
            host=MongoSettings().CONNECTION_STRING.get_secret_value(),
            uuidRepresentation="standard",
        )


def ensure_main_db_connection() -> None:
    """Register the main MongoDB connection (idempotent).

    The RAG pipeline's schedule and NATS sensor enumerate ``BucketEntity`` from the Dagster
    process, which needs the ``default`` mongoengine alias registered first.
    """
    _ensure_connection()


def _get_or_create_bucket(bucket_name: str, auto_sync: bool) -> BucketEntity:
    try:
        return BucketEntity.get_bucket_by_bucket_name(bucket_name, db_alias=_DB_ALIAS)
    except DoesNotExist:
        return BucketEntity.create_bucket(
            bucket_name=bucket_name, db_name=bucket_name, auto_sync=auto_sync, db_alias=_DB_ALIAS
        )


def _get_or_create_namespace(bucket_entity: BucketEntity, directory_name: str) -> NamespaceEntity:
    bucket_id = str(bucket_entity.id)
    try:
        return NamespaceEntity.get_namespace_by_bucket_and_folder(
            bucket_id=bucket_id, folder_name=directory_name, db_alias=_DB_ALIAS
        )
    except DoesNotExist:
        return NamespaceEntity.create_namespace(
            bucket_id=bucket_id, namespace_name=directory_name, folder_name=directory_name, db_alias=_DB_ALIAS
        )


def get_db_name_from_bucket_name(bucket_name: str, auto_sync: bool = False) -> str:
    """
    Get the database name (vector/doc store name) from the bucket name (container name).
    If the bucket doesn't exist in the database, creates a new bucket entry with db_name = bucket_name as default.

    Set auto_sync to True for autoloading pipelines (e.g. SharePoint to data lake) that automatically ingest data into
    the datalake. Set to False for manual pipelines (manual upload to data lake).
    """
    _ensure_connection()
    bucket_entity = _get_or_create_bucket(bucket_name=bucket_name, auto_sync=auto_sync)
    return bucket_entity.db_name


def get_or_create_namespace_for_directory(bucket_name: str, directory_name: str, auto_sync: bool = False) -> str:
    """
    Get or create namespace mapping for a directory within a bucket.
    """
    _ensure_connection()
    bucket_entity = _get_or_create_bucket(bucket_name=bucket_name, auto_sync=auto_sync)
    namespace_entity = _get_or_create_namespace(bucket_entity=bucket_entity, directory_name=directory_name)
    return namespace_entity.namespace_name
