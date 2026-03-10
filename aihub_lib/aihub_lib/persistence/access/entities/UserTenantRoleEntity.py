import logging
from datetime import UTC, datetime
from typing import Self

from mongoengine import DateTimeField, Document, ListField, NotUniqueError, StringField
from mongoengine.connection import get_db

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)


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

    user_id = StringField(required=True)
    tenant_id = StringField(required=True)
    roles = ListField(StringField(), default=list)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def get_by_user_and_tenant(cls, user_id: str, tenant_id: str) -> Self | None:
        """Fetches the user-tenant-role association. Returns None if not found."""
        return cls.objects(user_id=user_id, tenant_id=tenant_id).first()

    @classmethod
    @trace_fn
    def get_roles_for_user_in_tenant(cls, user_id: str, tenant_id: str) -> list[str]:
        """Returns the list of role names for a user in a specific tenant."""
        association = cls.get_by_user_and_tenant(user_id, tenant_id)
        return association.roles if association else []

    @classmethod
    def _validate_roles(cls, roles: list[str], tenant_id: str) -> list[str]:
        """
        Validates role names and returns only those that exist in the database.

        Logs a warning for any invalid roles that were provided.
        """
        # Runtime import: UserTenantRoleEntity ↔ RoleEntity mutual reference
        from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity

        valid_roles = RoleEntity.filter_existing_roles(roles, tenant_id)
        invalid_roles = set(roles) - set(valid_roles)
        if invalid_roles:
            logger.warning(
                f"Ignoring non-existent roles for user in tenant {tenant_id}: {sorted(invalid_roles)}. "
                f"Valid roles: {sorted(valid_roles)}"
            )
        return valid_roles

    @classmethod
    @trace_fn
    def create_or_update(
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
        validated_roles = cls._validate_roles(roles, tenant_id) if validate_roles else roles

        existing = cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            existing.roles = validated_roles
            existing.updated_at = datetime.now(UTC)
            existing.save()
            return existing

        try:
            association = cls(
                user_id=user_id,
                tenant_id=tenant_id,
                roles=validated_roles,
            )
            association.save()
            return association
        except NotUniqueError:
            existing = cls.get_by_user_and_tenant(user_id, tenant_id)
            if existing:
                existing.roles = validated_roles
                existing.updated_at = datetime.now(UTC)
                existing.save()
                return existing
            raise

    @classmethod
    @trace_fn
    def add_roles(cls, user_id: str, tenant_id: str, roles_to_add: list[str], validate_roles: bool = True) -> Self:
        """
        Adds roles to a user in a tenant. Creates the association if it doesn't exist.

        When validate_roles is True (default), only roles that exist in the database
        will be added. Invalid roles are logged as warnings and ignored.
        """
        validated_roles = cls._validate_roles(roles_to_add, tenant_id) if validate_roles else roles_to_add

        existing = cls.get_by_user_and_tenant(user_id, tenant_id)
        if existing:
            current_roles = set(existing.roles)
            current_roles.update(validated_roles)
            existing.roles = list(current_roles)
            existing.updated_at = datetime.now(UTC)
            existing.save()
            return existing

        return cls.create_or_update(user_id, tenant_id, validated_roles, validate_roles=False)

    @classmethod
    @trace_fn
    def get_user_ids_in_tenant(cls, tenant_id: str) -> list[str]:
        """Returns the list of user IDs that belong to a specific tenant."""
        return [assoc.user_id for assoc in cls.objects(tenant_id=tenant_id).only("user_id")]

    @classmethod
    @trace_fn
    def remove_roles(cls, user_id: str, tenant_id: str, roles_to_remove: list[str]) -> Self | None:
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

            # Clear active tenant if it matches the removed tenant
            # Direct collection access avoids circular import with UserEntity
            get_db()["users"].update_one(
                {"_id": user_id, "active_tenant_id": tenant_id},
                {"$set": {"active_tenant_id": None}},
            )
            return True
        return False
