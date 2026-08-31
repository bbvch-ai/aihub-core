"""
Database initialization module for the AI-Hub.

This module provides functions to initialize the database with required initial state,
including tenants, roles, permissions, and other essential entities needed for the hub to operate.
"""

import logging
from datetime import UTC, datetime, timedelta

from keycloak import KeycloakGetError
from mongoengine import DoesNotExist
from pydantic import BaseModel
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.auth.superuser_settings import SuperuserSettings
from swiss_ai_hub.core.infrastructure import AIHubSettings, StartupTenantSettings, UserSignupSettings, no_trace
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import BucketEntity, IngestorType, NamespaceEntity

logger = logging.getLogger(__name__)


class _DefaultRoleDefinition(BaseModel):
    name: str
    description: str
    access_rules: list[str]


async def _backfill_existing_users_into_startup_group(tenant_id: str) -> None:
    """One-time backfill: adds all pre-existing realm users to the startup tenant group.

    Keycloak's defaultGroups only affects users created after the group is configured.
    Users that already existed in the realm (e.g. the seeded admin from the realm import)
    need to be added explicitly. Only runs the first time the startup tenant is created —
    never on subsequent startups, so admin-initiated removals are not reverted.
    """
    all_users = await KeycloakAdminService.get_all_users()
    for user in all_users:
        await KeycloakAdminService.assign_user_to_tenant(user.id, tenant_id)
        logger.info(f"Backfilled user '{user.username}' into startup tenant group")


_DEFAULT_ROLE_DEFINITIONS: list[_DefaultRoleDefinition] = [
    _DefaultRoleDefinition(
        name="AIHubUser",
        description="Grants global user access to AI-Hub",
        access_rules=["aihub.user.>"],
    ),
    _DefaultRoleDefinition(
        name="AIHubAdmin",
        description="Grants global administrative access to AI-Hub",
        access_rules=["aihub.admin.>"],
    ),
    _DefaultRoleDefinition(
        name="AIHubAgentUser",
        description="Grants access to all agents but to nothing else",
        access_rules=["aihub.user.agent.>"],
    ),
    _DefaultRoleDefinition(
        name="AIHubAgentAdmin",
        description="Grants admin access to all agents but to nothing else",
        access_rules=["aihub.admin.agent.>"],
    ),
    _DefaultRoleDefinition(
        name="AIHubKnowledgeAdmin",
        description="Grants admin access to knowledge and agents",
        # Both forms are needed: ``knowledge.>`` covers every existing database, while the bare
        # ``knowledge`` root is what creating a new one is guarded on — a database that does not exist
        # yet cannot be named by a rule.
        access_rules=["aihub.admin.agent.>", "aihub.admin.knowledge", "aihub.admin.knowledge.>"],
    ),
    _DefaultRoleDefinition(
        name="AIHubProcessUser",
        description="Grants access to all processes but to nothing else",
        access_rules=["aihub.user.process.>"],
    ),
    _DefaultRoleDefinition(
        name="AIHubProcessAdmin",
        description="Grants admin access to all processes but to nothing else",
        access_rules=["aihub.admin.process.>"],
    ),
]


@no_trace
async def initialize_startup_tenant() -> TenantMetadataEntity | None:
    """
    Initialize the startup tenant for the platform.

    Creates the MongoDB tenant metadata and ensures a matching Keycloak group exists
    under /tenants/<tenant-name>. The Keycloak realm configures this group as a
    default group so all new users are automatically members. Also seeds the
    tenant's default role set (idempotent, gated by ``CREATE_DEFAULT_ROLES``).
    """
    settings = StartupTenantSettings()

    existing_tenant = TenantMetadataEntity.get_startup_tenant_metadata()
    if existing_tenant:
        logger.info(
            f"Startup tenant '{existing_tenant.name}' (id={existing_tenant.id}) already exists, skipping creation"
        )
        await initialize_default_roles_for_tenant(str(existing_tenant.id))
        return existing_tenant

    tenant = TenantMetadataEntity.ensure_startup_tenant_metadata_exists(
        tenant_id=settings.ID,
        name=settings.NAME,
        description=settings.DESCRIPTION,
        access_rules=settings.access_rules_list,
    )
    logger.info(f"Successfully created startup tenant '{tenant.name}' (id={tenant.id})")

    try:
        await KeycloakAdminService.create_tenant_group(tenant.id)
        logger.info(f"Keycloak tenant group '/tenants/{tenant.id}' created")
        await _backfill_existing_users_into_startup_group(tenant.id)
        await KeycloakAdminService.assign_superuser_to_tenant(tenant.id)
    except KeycloakGetError:
        logger.warning(
            f"Could not sync Keycloak group for tenant '{tenant.name}'"
            " - Keycloak may not have the required permissions yet"
        )

    await initialize_default_roles_for_tenant(str(tenant.id))
    return tenant


def _reconcile_default_role_rules(
    existing: RoleEntity, role_def: _DefaultRoleDefinition, tenant_id: str
) -> None:
    """Adds access rules a default role definition gained since the role row was seeded.

    Purely additive: rules an admin added by hand are kept, because the platform cannot tell a
    deliberate customization from stale state. Without this, a deployment that seeded its roles
    before a guard was introduced keeps a role that no longer grants what its name promises —
    ``AIHubKnowledgeAdmin`` without the ``aihub.admin.knowledge`` root, for instance, cannot
    create a database.
    """
    missing = [rule for rule in role_def.access_rules if rule not in existing.access_rules]
    if not missing:
        logger.info(f"Role '{role_def.name}' already exists for tenant '{tenant_id}', skipping creation")
        return
    existing.access_rules = list(existing.access_rules) + missing
    existing.save()
    logger.info(f"Added missing access rules {missing} to existing role '{role_def.name}' for tenant '{tenant_id}'")


@no_trace
async def initialize_default_roles_for_tenant(tenant_id: str) -> None:
    """
    Seed the default role set for a tenant. Idempotent.

    Roles that already exist are reconciled additively, so a deployment seeded before a
    definition gained a rule picks that rule up on the next startup.

    Gated by ``AIHubSettings().CREATE_DEFAULT_ROLES``: when disabled, tenants
    start empty and an admin is expected to create roles manually.
    """
    if not AIHubSettings().CREATE_DEFAULT_ROLES:
        logger.info(f"CREATE_DEFAULT_ROLES disabled; skipping default role seeding for tenant '{tenant_id}'")
        return

    for role_def in _DEFAULT_ROLE_DEFINITIONS:
        existing = RoleEntity.objects(name=role_def.name, tenant_id=tenant_id).first()
        if existing:
            _reconcile_default_role_rules(existing, role_def, tenant_id)
            continue
        try:
            RoleEntity.create_tenant_role(
                name=role_def.name,
                description=role_def.description,
                access_rules=role_def.access_rules,
                tenant_id=tenant_id,
            )
            logger.info(f"Successfully created role '{role_def.name}' for tenant '{tenant_id}'")
        except Exception:
            logger.exception(f"Failed to create role '{role_def.name}' for tenant '{tenant_id}'")
            raise


@no_trace
async def finalize_role_setup() -> None:
    """Runs post-tenant-initialization role checks and superuser bookkeeping."""
    await _validate_signup_roles()
    await initialize_superuser_token()


async def _validate_signup_roles() -> None:
    settings = UserSignupSettings()
    all_configured_roles = set(settings.regular_user_roles_list + settings.first_admin_user_roles_list)

    startup_tenant = TenantMetadataEntity.get_startup_tenant_metadata()
    tenant_id = str(startup_tenant.id) if startup_tenant else ""

    existing_roles = set(RoleEntity.filter_existing_roles(list(all_configured_roles), tenant_id))
    missing_roles = all_configured_roles - existing_roles

    if missing_roles:
        raise RuntimeError(
            f"Configured signup roles do not exist in the startup tenant: {sorted(missing_roles)}. "
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
            f"SUPERUSER_ROLES_JSON must contain '{SYS_ADMIN_ROLE}' so the seeded superuser has sysadmin access "
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

    await KeycloakAdminService.ensure_active_tenant(keycloak_user.id)


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
        {
            "bucket_name": settings.DEFAULT_BUCKET_NAME,
            "namespace": settings.DEFAULT_NAMESPACE_NAME,
            "ingestor": IngestorType.DEFAULT_RAG.value,
        },
        {
            "bucket_name": settings.SHARED_BUCKET_NAME,
            "namespace": settings.SHARED_NAMESPACE_NAME,
            "ingestor": IngestorType.SHARED_RAG.value,
        },
    ]

    for config in buckets_config:
        bucket = await _ensure_bucket_exists(config["bucket_name"], config["ingestor"])
        await _ensure_namespace_exists(bucket, config["namespace"])

    logger.info("Knowledge bucket initialization completed successfully")


async def _ensure_bucket_exists(bucket_name: str, ingestor: str) -> BucketEntity:
    """Ensure a bucket exists in the database with the correct ingestor, creating it if necessary.

    The ``ingestor`` is re-asserted on existing rows so the two seeded buckets are labelled with the legacy
    pipeline that owns them. This is labelling, not a safety net: rows predating the field read the inert
    ``unassigned`` default, so no pipeline claims them even if this seeder never runs (e.g. when
    ``CREATE_DEFAULT_BUCKETS`` is off).
    """
    try:
        bucket = BucketEntity.get_bucket_by_bucket_name(bucket_name)
        if bucket.ingestor != ingestor:
            bucket = BucketEntity.update_bucket(str(bucket.id), ingestor=ingestor)
            logger.info(f"Updated bucket '{bucket_name}' ingestor to '{ingestor}'")
        else:
            logger.info(f"Bucket '{bucket_name}' already exists, skipping creation")
        return bucket
    except DoesNotExist:
        try:
            bucket = BucketEntity.create_bucket(bucket_name=bucket_name, db_name=bucket_name, ingestor=ingestor)
            logger.info(f"Successfully created bucket '{bucket_name}'")
            return bucket
        except Exception:
            logger.exception(f"Failed to create bucket '{bucket_name}'")
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
        except Exception:
            logger.exception(f"Failed to create namespace '{namespace_name}' in bucket '{bucket.bucket_name}'")
            raise
