import logging
from datetime import UTC, datetime
from typing import Self

from beanie import Delete, Document, Insert, Replace, Save, SaveChanges, after_event
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ASCENDING, IndexModel
from pymongo.errors import DuplicateKeyError

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook

logger = logging.getLogger(__name__)


class TenantRolesByUser(BaseModel):
    """Batch lookup of user roles within a single tenant.

    Wraps ``{user_id: [role_name, ...]}`` so callers get a typed surface instead of
    a raw dict. Users with no row in the tenant default to an empty role list.
    """

    roles_by_user: dict[str, list[str]]

    def get_roles(self, user_id: str) -> list[str]:
        return self.roles_by_user.get(user_id, [])


class UserTenantRoleEntity(Document):
    """
    Represents the association between a user, a tenant, and their roles within that tenant.

    This entity enables multi-tenant role management where:
    - Users can belong to multiple tenants
    - Users can have different roles in each tenant
    - Roles are stored as a list of role names that reference RoleEntity documents

    Unknown fields are kept (`extra="allow"`): the MongoEngine document ran `strict: False`.
    """

    model_config = ConfigDict(extra="allow")

    user_id: str
    tenant_id: str
    roles: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "user_tenant_roles"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [
            IndexModel([("user_id", ASCENDING), ("tenant_id", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING)]),
            IndexModel([("roles", ASCENDING)]),
        ]

    @after_event(Insert, Replace, Save, SaveChanges, Delete)
    def _resync_openwebui_access(self) -> None:
        AccessChangeHook.notify()

    @classmethod
    @trace_fn
    async def get_by_user_and_tenant(cls, user_id: str, tenant_id: str) -> Self | None:
        """Fetches the user-tenant-role association. Returns None if not found."""
        return await cls.find_one({"user_id": user_id, "tenant_id": tenant_id})

    @classmethod
    @trace_fn
    async def get_roles_for_user_in_tenant(cls, user_id: str, tenant_id: str) -> list[str]:
        """Returns the list of role names for a user in a specific tenant."""
        association = await cls.get_by_user_and_tenant(user_id, tenant_id)
        return association.roles if association else []

    @classmethod
    async def _validate_roles(cls, roles: list[str], tenant_id: str) -> list[str]:
        """
        Validates role names and returns only those that exist in the database.

        Logs a warning for any invalid roles that were provided.
        """
        # Runtime import: UserTenantRoleEntity ↔ RoleEntity mutual reference
        from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

        valid_roles = await RoleEntity.filter_existing_roles(roles, tenant_id)
        invalid_roles = set(roles) - set(valid_roles)
        if invalid_roles:
            logger.warning(
                f"Ignoring non-existent roles for user in tenant {tenant_id}: {sorted(invalid_roles)}. "
                f"Valid roles: {sorted(valid_roles)}"
            )
        return valid_roles

    async def _set_roles(self, roles: list[str]) -> Self:
        self.roles = roles
        self.updated_at = datetime.now(UTC)
        await self.save_changes()
        return self

    @classmethod
    @trace_fn
    async def create_or_update(
        cls,
        user_id: str,
        tenant_id: str,
        roles: list[str],
        validate_roles: bool = True,
    ) -> Self:
        """
        Creates or updates a user-tenant-role association.

        If the association already exists, the roles are updated.
        If it doesn't exist, a new association is created.

        When validate_roles is True (default), only roles that exist in the database
        (as system roles or tenant-specific roles) will be assigned. Invalid roles
        are logged as warnings and ignored.
        """
        validated_roles = await cls._validate_roles(roles, tenant_id) if validate_roles else roles

        existing = await cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            return await existing._set_roles(validated_roles)

        try:
            return await cls(user_id=user_id, tenant_id=tenant_id, roles=validated_roles).insert()
        except DuplicateKeyError:
            existing = await cls.get_by_user_and_tenant(user_id, tenant_id)
            if existing:
                return await existing._set_roles(validated_roles)
            raise

    @classmethod
    @trace_fn
    async def add_roles(
        cls, user_id: str, tenant_id: str, roles_to_add: list[str], validate_roles: bool = True
    ) -> Self:
        """
        Adds roles to a user in a tenant. Creates the association if it doesn't exist.

        When validate_roles is True (default), only roles that exist in the database
        will be added. Invalid roles are logged as warnings and ignored.
        """
        validated_roles = await cls._validate_roles(roles_to_add, tenant_id) if validate_roles else roles_to_add

        existing = await cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            return await existing._set_roles(list(set(existing.roles) | set(validated_roles)))

        return await cls.create_or_update(user_id, tenant_id, validated_roles, validate_roles=False)

    @classmethod
    @trace_fn
    async def get_tenant_ids_for_user(cls, user_id: str) -> list[str]:
        """Returns the list of tenant IDs that a user belongs to."""
        return [association.tenant_id for association in await cls.find({"user_id": user_id}).to_list()]

    @classmethod
    @trace_fn
    async def get_user_ids_in_tenant(cls, tenant_id: str) -> list[str]:
        """Returns the list of user IDs that belong to a specific tenant."""
        return [association.user_id for association in await cls.find({"tenant_id": tenant_id}).to_list()]

    @classmethod
    @trace_fn
    async def get_user_ids_with_role(cls, tenant_id: str, role_name: str) -> list[str]:
        """Returns the IDs of the users holding the role in the tenant."""
        return [
            association.user_id
            for association in await cls.find({"tenant_id": tenant_id, "roles": role_name}).to_list()
        ]

    @classmethod
    @trace_fn
    async def get_roles_for_users_in_tenant(cls, user_ids: list[str], tenant_id: str) -> TenantRolesByUser:
        """Batch-loads tenant role lists for many users in one query."""
        if not user_ids:
            return TenantRolesByUser(roles_by_user={})
        associations = await cls.find({"user_id": {"$in": user_ids}, "tenant_id": tenant_id}).to_list()
        return TenantRolesByUser(
            roles_by_user={association.user_id: list(association.roles) for association in associations}
        )

    @classmethod
    @trace_fn
    async def remove_roles(cls, user_id: str, tenant_id: str, roles_to_remove: list[str]) -> Self | None:
        """Removes roles from a user in a tenant. Returns None if association doesn't exist."""
        existing = await cls.get_by_user_and_tenant(user_id, tenant_id)
        if not existing:
            return None
        return await existing._set_roles([r for r in existing.roles if r not in roles_to_remove])

    @classmethod
    @trace_fn
    async def remove_user_from_tenant(cls, user_id: str, tenant_id: str) -> bool:
        """Removes a user from a tenant entirely. Returns True if the association was deleted."""
        from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService

        existing = await cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            await existing.delete()

            active_tenant_id = await KeycloakAdminService.get_active_tenant_id(user_id)
            if active_tenant_id == tenant_id:
                await KeycloakAdminService.clear_active_tenant(user_id)

            return True
        return False

    @classmethod
    @trace_fn
    async def delete_memberships_of_tenant(cls, tenant_id: str) -> None:
        """Deletes every membership of the tenant in one query, for the tenant cascade.

        A query delete fires no document events, so the OpenWebUI re-sync MongoEngine's per-document signals gave
        is asked for here.
        """
        await cls.find({"tenant_id": tenant_id}).delete()
        AccessChangeHook.notify()
