"""
Database initialization module for the AI-Hub.

This module provides functions to initialize the database with required initial state,
including tenants, roles, permissions, and other essential entities needed for the hub to operate.
"""

import logging

from keycloak import KeycloakGetError
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.dependencies.superuser_auth_handler.superuser_settings import SuperuserSettings
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure import AIHubSettings, DefaultTenantSettings, UserSignupSettings, no_trace
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import BucketEntity, NamespaceEntity

logger = logging.getLogger(__name__)


async def _ensure_all_users_in_default_group(tenant_id: str) -> None:
    """Ensures all existing Keycloak users are members of the default tenant group.

    Keycloak's defaultGroups only applies to users created after the group is configured,
    so users from the realm import (e.g. the admin user) need to be added explicitly.
    """
    members = await KeycloakAdminService.get_tenant_members(tenant_id, offset=0, limit=1000)
    member_ids = {m.id for m in members}

    all_users = await KeycloakAdminService.get_all_users()
    for user in all_users:
        if user.id not in member_ids:
            await KeycloakAdminService.assign_user_to_tenant(user.id, tenant_id)
            logger.info(f"Added user '{user.username}' to default tenant group")


@no_trace
async def initialize_default_tenant() -> TenantEntity | None:
    """
    Initialize the default tenant for the platform.

    Creates the MongoDB tenant entity and ensures a matching Keycloak group exists
    under /tenants/<tenant-name>. The Keycloak realm configures this group as a
    default group so all new users are automatically members.
    """
    settings = DefaultTenantSettings()

    existing_tenant = TenantEntity.get_default_tenant()
    if existing_tenant:
        logger.info(
            f"Default tenant '{existing_tenant.name}' (id={existing_tenant.id}) already exists, skipping creation"
        )
    else:
        existing_tenant = TenantEntity.ensure_default_tenant_exists(
            tenant_id=settings.ID,
            name=settings.NAME,
            description=settings.DESCRIPTION,
            access_rules=settings.access_rules_list,
        )
        logger.info(f"Successfully created default tenant '{existing_tenant.name}' (id={existing_tenant.id})")

    # Ensure Keycloak user profile allows active_tenant_id attribute
    try:
        await KeycloakAdminService.ensure_user_profile_attributes()
    except Exception:
        logger.warning("Could not configure Keycloak user profile - active tenant attributes may not persist")

    # Ensure the matching Keycloak group exists and all realm users are members
    try:
        await KeycloakAdminService.create_tenant_group(existing_tenant.id)
        logger.info(f"Keycloak tenant group '/tenants/{existing_tenant.id}' ensured")
        await _ensure_all_users_in_default_group(existing_tenant.id)
    except KeycloakGetError:
        logger.warning(
            f"Could not sync Keycloak group for tenant '{existing_tenant.name}'"
            " - Keycloak may not have the required permissions yet"
        )

    return existing_tenant


@no_trace
async def initialize_roles() -> None:
    """
    Initialize all required system roles in the database.

    System roles are tenant-agnostic and available to all tenants.
    This function orchestrates the creation of all necessary roles
    for the AI-Hub to operate properly.
    """
    await initialize_system_role(
        name="AIHubSuperuser",
        description="Grants the AI-Hub Superuser global administrative access",
        access_rules=["aihub.admin.>"],
    )

    if AIHubSettings().CREATE_DEFAULT_ROLES:
        await initialize_system_role(
            name="AIHubUser",
            description="Grants global user access to AI-Hub",
            access_rules=["aihub.user.>"],
        )
        await initialize_system_role(
            name="AIHubAdmin",
            description="Grants global administrative access to AI-Hub",
            access_rules=["aihub.admin.>"],
        )
        await initialize_system_role(
            name="AIHubAgentUser",
            description="Grants access to all agents but to nothing else",
            access_rules=["aihub.user.agent.>"],
        )
        await initialize_system_role(
            name="AIHubAgentAdmin",
            description="Grants admin access to all agents but to nothing else",
            access_rules=["aihub.admin.agent.>"],
        )
        await initialize_system_role(
            name="AIHubKnowledgeAdmin",
            description="Grants admin access to knowledge and agents",
            access_rules=["aihub.admin.agent.>", "aihub.admin.knowledge.>"],
        )
        await initialize_system_role(
            name="AIHubProcessUser",
            description="Grants access to all processes but to nothing else",
            access_rules=["aihub.user.process.>"],
        )
        await initialize_system_role(
            name="AIHubProcessAdmin",
            description="Grants admin access to all processes but to nothing else",
            access_rules=["aihub.admin.process.>"],
        )

    logger.info("Role initialization completed successfully")

    # Validate that all configured signup roles exist in the database
    await _validate_signup_roles()

    # Initialize superuser if enabled
    await initialize_superuser()


async def _validate_signup_roles() -> None:
    settings = UserSignupSettings()
    all_configured_roles = set(settings.regular_user_roles_list + settings.first_admin_user_roles_list)

    default_tenant = TenantEntity.get_default_tenant()
    tenant_id = str(default_tenant.id) if default_tenant else ""

    existing_roles = set(RoleEntity.filter_existing_roles(list(all_configured_roles), tenant_id))
    missing_roles = all_configured_roles - existing_roles

    if missing_roles:
        raise RuntimeError(
            f"Configured signup roles do not exist in the database: {sorted(missing_roles)}. "
            f"Check AIHUB_USER_SIGNUP_REGULAR_USER_ROLES and AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES settings."
        )

    logger.info(f"All configured signup roles validated: {sorted(all_configured_roles)}")


async def initialize_system_role(name: str, description: str, access_rules: list[str]) -> None:
    """
    Initialize a system-wide role in the database if it doesn't already exist.

    System roles have tenant_id=None and are available to all tenants.
    This is idempotent and safe to call multiple times.
    """
    existing_role = RoleEntity.get_system_role_by_name(name)

    if existing_role:
        logger.info(f"System role '{name}' already exists, skipping creation")
        return

    try:
        RoleEntity.create_system_role(name=name, description=description, access_rules=access_rules)
        logger.info(f"Successfully created system role '{name}'")
    except Exception as e:
        logger.error(f"Failed to create system role '{name}': {e}")
        raise


async def initialize_superuser() -> None:
    """
    Initialize the superuser.

    The superuser uses a virtual tenant and does not need a user record.
    This is a no-op now that UserEntity is no longer used.
    """
    settings = SuperuserSettings()
    logger.info(f"Superuser initialization completed for user '{settings.NAME}'")
    logger.info("Note: Superuser operates with virtual tenant (full admin access)")


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
