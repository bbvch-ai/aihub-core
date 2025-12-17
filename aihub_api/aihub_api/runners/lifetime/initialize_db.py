"""
Database initialization module for the AI-Hub.

This module provides functions to initialize the database with required initial state,
including roles, permissions, and other essential entities needed for the hub to operate.
"""

import logging

from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.no_trace import no_trace
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from aihub_lib.persistence.user.UserEntity import UserEntity
from mongoengine import DoesNotExist

logger = logging.getLogger(__name__)


@no_trace
async def initialize_roles() -> None:
    """
    Initialize all required roles in the database.

    This function orchestrates the creation of all necessary roles
    for the AI-Hub to operate properly.
    """
    if SuperuserSettings().ENABLED:
        await initialize_role(
            name="AIHubSuperuser",
            description="Grants the AI-Hub Superuser global administrative access",
            access_rules=["aihub.admin.>"],
        )

    if AIHubSettings().CREATE_DEFAULT_ROLES:
        await initialize_role(
            name="AIHubUser",
            description="Grants global user access to AI-Hub",
            access_rules=["aihub.user.>"],
        )
        await initialize_role(
            name="AIHubAdmin",
            description="Grants global administrative access to AI-Hub",
            access_rules=["aihub.admin.>"],
        )
        await initialize_role(
            name="AIHubAgentUser",
            description="Grants access to all agents but to nothing else",
            access_rules=["aihub.user.agent.>"],
        )
        await initialize_role(
            name="AIHubAgentAdmin",
            description="Grants admin access to all agents but to nothing else",
            access_rules=["aihub.admin.agent.>"],
        )
        await initialize_role(
            name="AIHubKnowledgeAdmin",
            description="Grants admin access to knowledge and agents",
            access_rules=["aihub.admin.agent.>", "aihub.admin.knowledge.>"],
        )
        await initialize_role(
            name="AIHubProcessUser",
            description="Grants access to all processes but to nothing else",
            access_rules=["aihub.user.process.>"],
        )
        await initialize_role(
            name="AIHubProcessAdmin",
            description="Grants admin access to all processes but to nothing else",
            access_rules=["aihub.admin.process.>"],
        )

    logger.info("Role initialization completed successfully")

    # Initialize superuser if enabled
    await initialize_superuser()


async def initialize_role(name: str, description: str, access_rules: list[str]) -> None:
    """
    Initialize a single role in the database if it doesn't already exist.

    This is a generic function that can be used to create any role with
    the specified permissions. It is idempotent and safe to call multiple times.
    """
    # Check if the role already exists
    existing_role = RoleEntity.get_role_by_name(name)

    if existing_role:
        logger.info(f"Role '{name}' already exists, skipping creation")
        return

    # Create the new role
    role = RoleEntity(name=name, description=description, access_rules=access_rules)

    try:
        role.save()
        logger.info(f"Successfully created role '{name}'")
    except Exception as e:
        logger.error(f"Failed to create role '{name}': {e}")
        raise


async def initialize_superuser() -> None:
    """
    Initialize the superuser in the database if superuser auth is enabled.

    This function ensures that the superuser account exists in the database
    when the SuperuserAuthHandler is enabled.
    """
    if not SuperuserSettings().ENABLED:
        logger.info("Superuser is not enabled, skipping initialization")
        return

    try:
        settings = SuperuserSettings()
        user_identity = settings.get_user_identity()

        UserEntity.ensure_user_exists(
            oid=user_identity.id,
            name=user_identity.name,
            email=user_identity.email,
            roles=user_identity.roles,
            profile_image=user_identity.profile_image,
        )

        logger.info(f"Superuser initialization completed for user '{user_identity.name}'")

    except Exception as e:
        logger.error(f"Failed to initialize superuser: {e}")
        raise


@no_trace
async def initialize_knowledge_buckets() -> None:
    """
    Initialize the default knowledge buckets and namespaces.

    Creates the required bucket and namespace entries in MongoDB for the RAG system.
    S3 buckets are created separately by the init-buckets.sh script.
    """
    settings = AIHubSettings()

    if not settings.CREATE_DEFAULT_BUCKETS:
        logger.info("Bucket initialization disabled, skipping")
        return

    buckets_config = [
        {"bucket_name": settings.DEFAULT_BUCKET_NAME, "namespace": settings.DEFAULT_NAMESPACE_NAME},
        {"bucket_name": settings.SHARED_BUCKET_NAME, "namespace": settings.SHARED_NAMESPACE_NAME},
    ]

    for config in buckets_config:
        bucket = await _ensure_bucket_exists(config["bucket_name"])
        await _ensure_namespace_exists(bucket, config["namespace"])

    logger.info("Knowledge bucket initialization completed successfully")


async def _ensure_bucket_exists(bucket_name: str) -> BucketEntity:
    """Ensure a bucket exists in the database, creating it if necessary."""
    try:
        bucket = BucketEntity.get_bucket_by_bucket_name(bucket_name)
        logger.info(f"Bucket '{bucket_name}' already exists, skipping creation")
        return bucket
    except DoesNotExist:
        try:
            bucket = BucketEntity.create_bucket(bucket_name=bucket_name, db_name=bucket_name)
            logger.info(f"Successfully created bucket '{bucket_name}'")
            return bucket
        except Exception as e:
            logger.error(f"Failed to create bucket '{bucket_name}': {e}")
            raise


async def _ensure_namespace_exists(bucket: BucketEntity, namespace_name: str) -> NamespaceEntity:
    """Ensure a namespace exists for the given bucket, creating it if necessary."""
    bucket_id = str(bucket.id)
    try:
        namespace = NamespaceEntity.get_namespace_by_bucket_and_name(bucket_id=bucket_id, namespace_name=namespace_name)
        logger.info(f"Namespace '{namespace_name}' already exists in bucket '{bucket.bucket_name}', skipping creation")
        return namespace
    except DoesNotExist:
        try:
            namespace = NamespaceEntity.create_namespace(
                bucket_id=bucket_id,
                namespace_name=namespace_name,
                folder_name=namespace_name,
            )
            logger.info(f"Successfully created namespace '{namespace_name}' in bucket '{bucket.bucket_name}'")
            return namespace
        except Exception as e:
            logger.error(f"Failed to create namespace '{namespace_name}' in bucket '{bucket.bucket_name}': {e}")
            raise
