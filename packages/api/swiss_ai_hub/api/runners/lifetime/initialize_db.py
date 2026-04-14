"""
Database initialization module for the AI-Hub.

This module provides functions to initialize the database with required initial state,
including tenants, roles, permissions, and other essential entities needed for the hub to operate.
"""

import logging
from datetime import UTC, datetime, timedelta

from keycloak import KeycloakGetError
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.auth.superuser_settings import SuperuserSettings
from swiss_ai_hub.core.infrastructure import AIHubSettings, DefaultTenantSettings, UserSignupSettings, no_trace
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import BucketEntity, NamespaceEntity

logger = logging.getLogger(__name__)


async def _backfill_existing_users_into_default_group(tenant_id: str) -> None:
    """One-time backfill: adds all pre-existing realm users to the default tenant group.

    Keycloak's defaultGroups only affects users created after the group is configured.
    Users that already existed in the realm (e.g. the seeded admin from the realm import)
    need to be added explicitly. Only runs the first time the default tenant is created —
    never on subsequent startups, so admin-initiated removals are not reverted.
    """
    all_users = await KeycloakAdminService.get_all_users()
    for user in all_users:
        await KeycloakAdminService.assign_user_to_tenant(user.id, tenant_id)
        logger.info(f"Backfilled user '{user.username}' into default tenant group")


_DEFAULT_ROLE_DEFINITIONS: list[tuple[str, str, list[str]]] = [
    ("AIHubUser", "Grants global user access to AI-Hub", ["aihub.user.>"]),
    ("AIHubAdmin", "Grants global administrative access to AI-Hub", ["aihub.admin.>"]),
    ("AIHubAgentUser", "Grants access to all agents but to nothing else", ["aihub.user.agent.>"]),
    ("AIHubAgentAdmin", "Grants admin access to all agents but to nothing else", ["aihub.admin.agent.>"]),
    (
        "AIHubKnowledgeAdmin",
        "Grants admin access to knowledge and agents",
        ["aihub.admin.agent.>", "aihub.admin.knowledge.>"],
    ),
    ("AIHubProcessUser", "Grants access to all processes but to nothing else", ["aihub.user.process.>"]),
    ("AIHubProcessAdmin", "Grants admin access to all processes but to nothing else", ["aihub.admin.process.>"]),
]


@no_trace
async def initialize_default_tenant() -> TenantMetadataEntity | None:
    """
    Initialize the default tenant for the platform.

    Creates the MongoDB tenant metadata and ensures a matching Keycloak group exists
    under /tenants/<tenant-name>. The Keycloak realm configures this group as a
    default group so all new users are automatically members. Also seeds the
    tenant's default role set (idempotent, gated by ``CREATE_DEFAULT_ROLES``).
    """
    settings = DefaultTenantSettings()

    existing_tenant = TenantMetadataEntity.get_default_tenant_metadata()
    if existing_tenant:
        logger.info(
            f"Default tenant '{existing_tenant.name}' (id={existing_tenant.id}) already exists, skipping creation"
        )
        await initialize_default_roles_for_tenant(str(existing_tenant.id))
        return existing_tenant

    tenant = TenantMetadataEntity.ensure_default_tenant_metadata_exists(
        tenant_id=settings.ID,
        name=settings.NAME,
        description=settings.DESCRIPTION,
        access_rules=settings.access_rules_list,
    )
    logger.info(f"Successfully created default tenant '{tenant.name}' (id={tenant.id})")

    try:
        await KeycloakAdminService.create_tenant_group(tenant.id)
        logger.info(f"Keycloak tenant group '/tenants/{tenant.id}' created")
        await _backfill_existing_users_into_default_group(tenant.id)
    except KeycloakGetError:
        logger.warning(
            f"Could not sync Keycloak group for tenant '{tenant.name}'"
            " - Keycloak may not have the required permissions yet"
        )

    await initialize_default_roles_for_tenant(str(tenant.id))
    return tenant


@no_trace
async def initialize_default_roles_for_tenant(tenant_id: str) -> None:
    """
    Seed the default role set for a tenant. Idempotent.

    Gated by ``AIHubSettings().CREATE_DEFAULT_ROLES``: when disabled, tenants
    start empty and an admin is expected to create roles manually.
    """
    if not AIHubSettings().CREATE_DEFAULT_ROLES:
        logger.info(f"CREATE_DEFAULT_ROLES disabled; skipping default role seeding for tenant '{tenant_id}'")
        return

    for name, description, access_rules in _DEFAULT_ROLE_DEFINITIONS:
        existing = RoleEntity.objects(name=name, tenant_id=tenant_id).first()
        if existing:
            logger.info(f"Role '{name}' already exists for tenant '{tenant_id}', skipping creation")
            continue
        try:
            RoleEntity.create_tenant_role(
                name=name,
                description=description,
                access_rules=access_rules,
                tenant_id=tenant_id,
            )
            logger.info(f"Successfully created role '{name}' for tenant '{tenant_id}'")
        except Exception as e:
            logger.error(f"Failed to create role '{name}' for tenant '{tenant_id}': {e}")
            raise


@no_trace
async def finalize_role_setup() -> None:
    """Runs post-tenant-initialization role checks and superuser bookkeeping."""
    await _validate_signup_roles()
    await initialize_superuser_token()


async def _validate_signup_roles() -> None:
    settings = UserSignupSettings()
    all_configured_roles = set(settings.regular_user_roles_list + settings.first_admin_user_roles_list)

    default_tenant = TenantMetadataEntity.get_default_tenant_metadata()
    tenant_id = str(default_tenant.id) if default_tenant else ""

    existing_roles = set(RoleEntity.filter_existing_roles(list(all_configured_roles), tenant_id))
    missing_roles = all_configured_roles - existing_roles

    if missing_roles:
        raise RuntimeError(
            f"Configured signup roles do not exist in the default tenant: {sorted(missing_roles)}. "
            f"Check AIHUB_USER_SIGNUP_REGULAR_USER_ROLES and AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES settings."
        )

    logger.info(f"All configured signup roles validated: {sorted(all_configured_roles)}")


_SUPERUSER_TOKEN_NAME = "superuser-static-token"
_SUPERUSER_TOKEN_TTL = timedelta(days=365 * 100)


async def initialize_superuser_token() -> None:
    """
    Ensures the superuser Keycloak user exists with the AIHubSysAdmin realm role,
    then upserts a ``BearerToken`` row holding the static ``SUPERUSER_TOKEN`` env
    var so internal services (OpenWebUI, RAG, images, audio, doc loader, Langfuse
    provisioner) can authenticate against the API as that user via
    ``TokenAuthHandler``.

    Fails loudly if the seeded Keycloak user is missing or lacks the sysadmin
    realm role — the platform cannot function correctly without it.
    """
    settings = SuperuserSettings()

    if SYS_ADMIN_ROLE not in settings.roles_list:
        raise RuntimeError(
            f"SUPERUSER_ROLES must contain '{SYS_ADMIN_ROLE}' so the seeded superuser has sysadmin access "
            f"(got: {settings.roles_list})."
        )

    try:
        keycloak_user = await KeycloakAdminService.find_user_by_email(settings.EMAIL)
    except KeycloakGetError as e:
        raise RuntimeError(
            f"Could not query Keycloak for superuser (email={settings.EMAIL}): {e}. "
            "Ensure the Keycloak realm import has completed before the API starts."
        ) from e

    if not keycloak_user:
        raise RuntimeError(
            f"Superuser not found in Keycloak (email={settings.EMAIL}). "
            "Ensure the realm import creates a user with this email."
        )

    BearerToken.upsert_static_token(
        name=_SUPERUSER_TOKEN_NAME,
        token_value=settings.TOKEN.get_secret_value(),
        expiry_date=datetime.now(UTC) + _SUPERUSER_TOKEN_TTL,
        user_oid=keycloak_user.id,
    )
    logger.info(f"Superuser bearer token seeded for Keycloak user '{settings.USERNAME}' (id={keycloak_user.id})")


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
