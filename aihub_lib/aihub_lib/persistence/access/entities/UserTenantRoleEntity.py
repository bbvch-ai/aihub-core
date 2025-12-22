from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from mongoengine import DateTimeField, Document, ListField, StringField

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class UserTenantRoleEntity(Document):
    """
    Represents the association between a user, a tenant, and their roles within that tenant.

    This entity enables multi-tenant role management where:
    - Users can belong to multiple tenants
    - Users can have different roles in each tenant
    - Roles are stored as a list of role names that reference RoleEntity documents
    """

    meta = {
        "collection": "user_tenant_roles",
        "strict": False,
        "indexes": [
            {"fields": ["user_id", "tenant_id"], "unique": True},
            {"fields": ["user_id"]},
            {"fields": ["tenant_id"]},
            {"fields": ["roles"]},
        ],
    }

    id = StringField(primary_key=True, default=lambda: str(uuid4()))
    user_id = StringField(required=True)
    tenant_id = StringField(required=True)
    roles = ListField(StringField(), default=list)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def get_by_user_and_tenant(cls, user_id: str, tenant_id: str) -> UserTenantRoleEntity | None:
        """Fetches the user-tenant-role association. Returns None if not found."""
        return cls.objects(user_id=user_id, tenant_id=tenant_id).first()

    @classmethod
    @trace_fn
    def get_roles_for_user_in_tenant(cls, user_id: str, tenant_id: str) -> list[str]:
        """Returns the list of role names for a user in a specific tenant."""
        association = cls.get_by_user_and_tenant(user_id, tenant_id)
        return association.roles if association else []

    @classmethod
    @trace_fn
    def get_all_roles_for_user(cls, user_id: str) -> dict[str, list[str]]:
        """Returns all roles for a user across all tenants, keyed by tenant_id."""
        associations = cls.objects(user_id=user_id)
        return {assoc.tenant_id: assoc.roles for assoc in associations}

    @classmethod
    @trace_fn
    def get_tenants_for_user(cls, user_id: str) -> list[str]:
        """Returns the list of tenant IDs that a user belongs to."""
        associations = cls.objects(user_id=user_id).only("tenant_id")
        return [assoc.tenant_id for assoc in associations]

    @classmethod
    @trace_fn
    def get_users_in_tenant(cls, tenant_id: str) -> list[str]:
        """Returns the list of user IDs in a specific tenant."""
        associations = cls.objects(tenant_id=tenant_id).only("user_id")
        return [assoc.user_id for assoc in associations]

    @classmethod
    @trace_fn
    def create_or_update(
        cls,
        user_id: str,
        tenant_id: str,
        roles: list[str],
    ) -> UserTenantRoleEntity:
        """
        Creates or updates a user-tenant-role association.

        If the association already exists, the roles are updated.
        If it doesn't exist, a new association is created.
        """
        existing = cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            existing.roles = roles
            existing.updated_at = datetime.now(UTC)
            existing.save()
            return existing

        association = cls(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
        )
        association.save()
        return association

    @classmethod
    @trace_fn
    def add_roles(cls, user_id: str, tenant_id: str, roles_to_add: list[str]) -> UserTenantRoleEntity:
        """Adds roles to a user in a tenant. Creates the association if it doesn't exist."""
        existing = cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            current_roles = set(existing.roles)
            current_roles.update(roles_to_add)
            existing.roles = list(current_roles)
            existing.updated_at = datetime.now(UTC)
            existing.save()
            return existing

        return cls.create_or_update(user_id, tenant_id, roles_to_add)

    @classmethod
    @trace_fn
    def remove_roles(cls, user_id: str, tenant_id: str, roles_to_remove: list[str]) -> UserTenantRoleEntity | None:
        """Removes roles from a user in a tenant. Returns None if association doesn't exist."""
        existing = cls.get_by_user_and_tenant(user_id, tenant_id)
        if not existing:
            return None

        existing.roles = [r for r in existing.roles if r not in roles_to_remove]
        existing.updated_at = datetime.now(UTC)
        existing.save()
        return existing

    @classmethod
    @trace_fn
    def remove_user_from_tenant(cls, user_id: str, tenant_id: str) -> bool:
        """Removes a user from a tenant entirely. Returns True if the association was deleted."""
        existing = cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            existing.delete()
            return True
        return False

    @classmethod
    @trace_fn
    def count_users_in_tenant(cls, tenant_id: str) -> int:
        """Count the number of users in a tenant."""
        return cls.objects(tenant_id=tenant_id).count()

    @classmethod
    @trace_fn
    def user_exists_in_any_tenant(cls, user_id: str) -> bool:
        """Check if a user exists in any tenant."""
        return cls.objects(user_id=user_id).count() > 0
