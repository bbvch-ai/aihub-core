from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from mongoengine import DoesNotExist, disconnect

from aihub_pipeline.util.connection_utils import connect_to_mongo_db


def get_db_name_from_bucket_name(bucket_name: str) -> str:
    """
    Get the database name (vector/doc store name) from the bucket name (container name).
    If the bucket doesn't exist in the database, creates a new bucket entry
    with db_name = bucket_name as default.
    """
    connect_to_mongo_db(AIHubSettings().MONGO_MAIN_DB_NAME)

    try:
        bucket_entity = BucketEntity.get_bucket_by_bucket_name(bucket_name)
        return bucket_entity.db_name
    except DoesNotExist:
        bucket_entity = BucketEntity.create_bucket(bucket_name=bucket_name, db_name=bucket_name)
        return bucket_entity.db_name
    finally:
        disconnect()


def get_or_create_namespace_for_directory(bucket_name: str, directory_name: str) -> str:
    """
    Get or create namespace mapping for a directory within a bucket.
    """
    connect_to_mongo_db(AIHubSettings().MONGO_MAIN_DB_NAME)

    try:
        try:
            bucket_entity = BucketEntity.get_bucket_by_bucket_name(bucket_name)
        except DoesNotExist:
            bucket_entity = BucketEntity.create_bucket(bucket_name=bucket_name, db_name=bucket_name)

        namespace_entity = NamespaceEntity.get_namespace_by_bucket_and_folder(
            bucket_id=str(bucket_entity.id), folder_name=directory_name
        )

        if not namespace_entity:
            namespace_entity = NamespaceEntity.create_namespace(
                bucket_id=str(bucket_entity.id), namespace_name=directory_name, folder_name=directory_name
            )

        return namespace_entity.namespace_name

    finally:
        disconnect()
