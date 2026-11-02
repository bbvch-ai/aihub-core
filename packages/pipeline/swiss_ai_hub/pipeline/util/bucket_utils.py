from mongoengine import DoesNotExist, NotUniqueError
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoConnectionRegistry
from swiss_ai_hub.core.persistence.rag.datalake.entities import BucketEntity, NamespaceEntity

from swiss_ai_hub.pipeline.util.namespace_collision_error import NamespaceCollisionError

# Default alias for the main database connection
_DB_ALIAS = "default"


def _ensure_connection() -> None:
    MongoConnectionRegistry.ensure_alias(AIHubSettings().MONGO_MAIN_DB_NAME, alias=_DB_ALIAS)


def ensure_main_db_connection() -> None:
    """Register the main MongoDB connection (idempotent).

    The document ingestion pipeline's schedule and NATS sensor enumerate ``BucketEntity`` from the Dagster
    process, which needs the ``default`` mongoengine alias registered first.
    """
    _ensure_connection()


def _get_or_create_bucket(bucket_name: str) -> BucketEntity:
    try:
        return BucketEntity.get_bucket_by_bucket_name(bucket_name, db_alias=_DB_ALIAS)
    except DoesNotExist:
        return BucketEntity.create_bucket(bucket_name=bucket_name, db_name=bucket_name, db_alias=_DB_ALIAS)


def _get_or_create_namespace(bucket_entity: BucketEntity, directory_name: str) -> NamespaceEntity:
    """A concurrent observation of the same database may create the namespace between the lookup and the insert;
    the unique index then rejects ours, and the re-read returns theirs."""
    bucket_id = str(bucket_entity.id)
    try:
        return _namespace_of_folder(bucket_id, directory_name)
    except DoesNotExist:
        pass
    try:
        return NamespaceEntity.create_namespace(
            bucket_id=bucket_id, namespace_name=directory_name, folder_name=directory_name, db_alias=_DB_ALIAS
        )
    except NotUniqueError:
        return _namespace_of_folder(bucket_id, directory_name)


def _namespace_of_folder(bucket_id: str, directory_name: str) -> NamespaceEntity:
    """The folder that registered its name first keeps the namespace; a later folder that sanitises to the same
    name is refused, because one namespace can only track one folder. Raises ``DoesNotExist`` when neither the
    folder nor its name is registered yet."""
    try:
        return NamespaceEntity.get_namespace_by_bucket_and_folder(
            bucket_id=bucket_id, folder_name=directory_name, db_alias=_DB_ALIAS
        )
    except DoesNotExist:
        pass
    namespace_name = NamespaceEntity.sanitize_namespace_name(directory_name)
    owner = NamespaceEntity.get_namespace_by_bucket_and_name(
        bucket_id=bucket_id, namespace_name=namespace_name, db_alias=_DB_ALIAS
    )
    raise NamespaceCollisionError(
        directory=directory_name, existing_folder=owner.folder_name, namespace_name=namespace_name
    )


def get_db_name_from_bucket_name(bucket_name: str) -> str:
    """
    Get the database name (vector/doc store name) from the bucket name (container name).
    If the bucket doesn't exist in the database, creates a new bucket entry with db_name = bucket_name as default.
    """
    _ensure_connection()
    bucket_entity = _get_or_create_bucket(bucket_name=bucket_name)
    return bucket_entity.db_name


def get_or_create_namespace_for_directory(bucket_name: str, directory_name: str) -> str:
    """
    Get or create namespace mapping for a directory within a bucket.

    Raises ``NamespaceCollisionError`` when the directory sanitises to a namespace another directory owns.
    """
    _ensure_connection()
    bucket_entity = _get_or_create_bucket(bucket_name=bucket_name)
    namespace_entity = _get_or_create_namespace(bucket_entity=bucket_entity, directory_name=directory_name)
    return namespace_entity.namespace_name
