import logging

import mongoengine
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.DatalakeFileEntity import DatalakeFileEntity
from mongoengine import register_connection
from mongoengine.errors import MongoEngineException
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

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


def _extract_bucket_name_from_uri(uri: str) -> str:
    return uri.replace("s3://", "").split("/")[0]


def _extract_file_path_from_uri(uri: str) -> str:
    parts = uri.replace("s3://", "").split("/", 1)
    return parts[1] if len(parts) > 1 else ""


def _get_entity(uri: str, namespace: str, create_if_missing: bool = False) -> DatalakeFileEntity | None:
    bucket_name = _extract_bucket_name_from_uri(uri)
    file_path = _extract_file_path_from_uri(uri)

    try:
        bucket = BucketEntity.get_bucket_by_bucket_name(bucket_name, db_alias=_DB_ALIAS)
    except BucketEntity.DoesNotExist:
        logger.warning(f"Bucket '{bucket_name}' not found, skipping status update for {uri}")
        return None

    bucket_id = str(bucket.id)

    if create_if_missing:
        return DatalakeFileEntity.get_or_create_file(
            bucket_id=bucket_id,
            namespace_name=namespace,
            file_path=file_path,
            db_alias=_DB_ALIAS,
        )

    try:
        return DatalakeFileEntity.get_file_by_path(bucket_id, namespace, file_path, db_alias=_DB_ALIAS)
    except DatalakeFileEntity.DoesNotExist:
        logger.debug(f"DatalakeFileEntity not found for {uri}")
        return None


def mark_file_processing(uri: str, namespace: str) -> DatalakeFileEntity | None:
    """Ensure file is tracked as PROCESSING when pipeline starts."""
    _ensure_connection()
    try:
        # get_or_create_file already sets status to PROCESSING
        entity = _get_entity(uri, namespace, create_if_missing=True)
        if entity:
            logger.debug(f"Tracked file as PROCESSING: {uri}")
        return entity
    except ValueError as e:
        logger.warning(f"Invalid file path for {uri}: {e}")
        return None
    except (PyMongoError, MongoEngineException) as e:
        logger.warning(f"Database error tracking file as processing: {uri}, error: {e}")
        return None


def mark_file_ingested(uri: str, namespace: str) -> DatalakeFileEntity | None:
    """Mark a datalake file as INGESTED after successful docstore insertion."""
    _ensure_connection()
    return _mark_entity_ingested(uri, namespace)


def mark_files_ingested(files: list[tuple[str, str]]) -> list[DatalakeFileEntity]:
    """Mark multiple datalake files as INGESTED in a single connection.

    Args:
        files: List of (uri, namespace) tuples to mark as ingested.

    Returns:
        List of successfully updated entities.
    """
    if not files:
        return []

    _ensure_connection()
    results = []
    for uri, namespace in files:
        entity = _mark_entity_ingested(uri, namespace)
        if entity:
            results.append(entity)
    return results


def _mark_entity_ingested(uri: str, namespace: str) -> DatalakeFileEntity | None:
    """Internal helper to mark a single entity as ingested (assumes connection exists)."""
    try:
        entity = _get_entity(uri, namespace)
        if entity:
            entity.mark_ingested()
            logger.debug(f"Marked file as INGESTED: {uri}")
        else:
            logger.debug(f"Cannot mark as ingested - entity not found for {uri}")
        return entity
    except (PyMongoError, MongoEngineException) as e:
        logger.warning(f"Database error marking file as ingested: {uri}, error: {e}")
        return None


def delete_file_entity(uri: str, namespace: str) -> bool:
    """Delete the DatalakeFileEntity tracking record for a file.

    Should be called when a file is deleted from the datalake through the pipeline.
    Manual deletion from S3 is not supported and will leave orphaned tracking records.
    """
    _ensure_connection()
    bucket_name = _extract_bucket_name_from_uri(uri)
    file_path = _extract_file_path_from_uri(uri)

    try:
        bucket = BucketEntity.get_bucket_by_bucket_name(bucket_name, db_alias=_DB_ALIAS)
    except BucketEntity.DoesNotExist:
        logger.warning(f"Bucket '{bucket_name}' not found, cannot delete entity for {uri}")
        return False

    bucket_id = str(bucket.id)

    try:
        deleted = DatalakeFileEntity.delete_by_path(bucket_id, namespace, file_path, db_alias=_DB_ALIAS)
        if deleted:
            logger.debug(f"Deleted DatalakeFileEntity for {uri}")
        else:
            logger.debug(f"No DatalakeFileEntity found to delete for {uri}")
        return deleted
    except (PyMongoError, MongoEngineException) as e:
        logger.warning(f"Database error deleting file entity: {uri}, error: {e}")
        return False
