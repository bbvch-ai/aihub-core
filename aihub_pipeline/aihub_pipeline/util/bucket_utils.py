from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from mongoengine import DoesNotExist, disconnect

from aihub_pipeline.util.connection_utils import connect_to_mongo_db


def _get_or_create_bucket(bucket_name: str, auto_sync: bool) -> BucketEntity:
    try:
        return BucketEntity.get_bucket_by_bucket_name(bucket_name)
    except DoesNotExist:
        return BucketEntity.create_bucket(bucket_name=bucket_name, db_name=bucket_name)


def _get_or_create_namespace(bucket_entity: BucketEntity, directory_name: str) -> NamespaceEntity:
    bucket_id = str(bucket_entity.id)
    try:
        return NamespaceEntity.get_namespace_by_bucket_and_folder(bucket_id=bucket_id, folder_name=directory_name)
    except DoesNotExist:
        return NamespaceEntity.create_namespace(
            bucket_id=bucket_id, namespace_name=directory_name, folder_name=directory_name
        )


def get_db_name_from_bucket_name(bucket_name: str, auto_sync: bool = False) -> str:
    """
    Get the database name (vector/doc store name) from the bucket name (container name).
    If the bucket doesn't exist in the database, creates a new bucket entry with db_name = bucket_name as default.

    Set auto_sync to True for autoloading pipelines (e.g. SharePoint to data lake) that automatically ingest data into
    the datalake. Set to False for manual pipelines (manual upload to data lake).
    """
    connect_to_mongo_db(AIHubSettings().MONGO_MAIN_DB_NAME)
    try:
        bucket_entity = _get_or_create_bucket(bucket_name=bucket_name, auto_sync=auto_sync)
        return bucket_entity.db_name
    finally:
        disconnect()


def get_or_create_namespace_for_directory(bucket_name: str, directory_name: str, auto_sync: bool = False) -> str:
    """
    Get or create namespace mapping for a directory within a bucket.
    """
    connect_to_mongo_db(AIHubSettings().MONGO_MAIN_DB_NAME)
    try:
        bucket_entity = _get_or_create_bucket(bucket_name=bucket_name, auto_sync=auto_sync)
        namespace_entity = _get_or_create_namespace(bucket_entity=bucket_entity, directory_name=directory_name)
        return namespace_entity.namespace_name
    finally:
        disconnect()
