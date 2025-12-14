"""
Knowledge initialization module for the AI-Hub.

This module initializes the default knowledge bucket and namespace at API startup.
It creates both the MongoDB entities (BucketEntity, NamespaceEntity) and ensures
the corresponding S3 bucket exists in SeaweedFS storage.
"""

import logging

from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.no_trace import no_trace
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from mongoengine import DoesNotExist

logger = logging.getLogger(__name__)


def _get_or_create_bucket(bucket_name: str) -> BucketEntity:
    """Get existing bucket or create a new one."""
    try:
        return BucketEntity.get_bucket_by_bucket_name(bucket_name)
    except DoesNotExist:
        logger.info(f"Creating default bucket '{bucket_name}' in MongoDB")
        return BucketEntity.create_bucket(bucket_name=bucket_name, db_name=bucket_name, auto_sync=False)


def _get_or_create_namespace(bucket: BucketEntity, namespace_name: str) -> NamespaceEntity:
    """Get existing namespace or create a new one."""
    bucket_id = str(bucket.id)
    try:
        return NamespaceEntity.get_namespace_by_bucket_and_name(bucket_id=bucket_id, namespace_name=namespace_name)
    except DoesNotExist:
        logger.info(f"Creating default namespace '{namespace_name}' in bucket '{bucket.bucket_name}'")
        return NamespaceEntity.create_namespace(
            bucket_id=bucket_id, namespace_name=namespace_name, folder_name=namespace_name
        )


def _ensure_s3_bucket_exists(s3_service: S3AnonymousFileAccessService, bucket_name: str) -> None:
    """Ensure the S3 bucket exists, creating it if necessary."""
    try:
        was_created = s3_service.ensure_bucket_exists(bucket_name)
        if was_created:
            logger.info(f"Created S3 bucket '{bucket_name}'")
    except Exception as e:
        logger.error(f"Failed to ensure S3 bucket '{bucket_name}' exists: {e}")


@no_trace
async def initialize_knowledge_buckets() -> None:
    """
    Initialize the default knowledge bucket and namespace.

    This function:
    1. Creates the default BucketEntity in MongoDB if it doesn't exist
    2. Creates the default NamespaceEntity in MongoDB if it doesn't exist
    3. Ensures the corresponding S3 bucket exists in SeaweedFS

    Controlled by AIHubSettings.CREATE_DEFAULT_KNOWLEDGE (default: True).
    This initialization is idempotent and safe to call multiple times.
    """
    settings = AIHubSettings()

    if not settings.CREATE_DEFAULT_KNOWLEDGE:
        logger.info("Default knowledge creation is disabled, skipping initialization")
        return

    bucket_name = settings.DEFAULT_KNOWLEDGE_BUCKET
    namespace_name = settings.DEFAULT_KNOWLEDGE_NAMESPACE

    bucket = _get_or_create_bucket(bucket_name)
    _get_or_create_namespace(bucket, namespace_name)

    try:
        s3_service = S3AnonymousFileAccessService()
        _ensure_s3_bucket_exists(s3_service, bucket_name)
    except Exception as e:
        logger.warning(f"S3 service not available, skipping S3 bucket creation: {e}")

    logger.info("Knowledge bucket initialization complete")
