from datetime import UTC, datetime
from typing import Self

from mongoengine import BooleanField, DateTimeField, Document, ListField, NotUniqueError, StringField

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class TenantMetadataEntity(Document):
    """
    Metadata (display name, description, access rules) for a tenant.

    WARNING: This collection is NOT the source of truth for tenant existence.
    Keycloak owns that — the group ``/tenants/<tenant_id>`` is the only authoritative
    signal that a tenant exists. Callers MUST verify existence via
    ``KeycloakAdminService.tenant_exists`` / ``get_tenant_group`` /
    ``filter_existing_tenant_ids`` before acting on a tenant. The methods on this
    class return metadata only; a returned entity does not imply the tenant still
    exists in Keycloak (it may be orphaned), and a missing entity does not imply
    the tenant is absent from Keycloak (it may be unconfigured).

    The id is a human-readable slug (e.g. "default") that matches the Keycloak group
    name under /tenants/. The name is a display name for the UI.
    """

    meta = {
        "collection": "tenants",
        "strict": False,
        "indexes": [
            {"fields": ["name"], "unique": True},
            {"fields": ["is_default"]},
        ],
    }

    id = StringField(primary_key=True)
    name = StringField(required=True, unique=True)
    description = StringField(default="")
    access_rules = ListField(StringField(), default=list)
    is_default = BooleanField(default=False)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def get_metadata_by_tenant_id(cls, tenant_id: str) -> Self | None:
        """Fetches tenant metadata by id. Returns None if no metadata is stored.

        Does NOT verify that the tenant exists in Keycloak — use
        ``KeycloakAdminService.tenant_exists`` for that.
        """
        return cls.objects(id=tenant_id).first()

    @classmethod
    @trace_fn
    def get_metadata_by_tenant_name(cls, name: str) -> Self | None:
        """Fetches tenant metadata by display name. Returns None if no metadata is stored.

        Does NOT verify that the tenant exists in Keycloak — use
        ``KeycloakAdminService.tenant_exists`` for that.
        """
        return cls.objects(name=name).first()

    @classmethod
    @trace_fn
    def get_default_tenant_metadata(cls) -> Self | None:
        """Fetches metadata for the default tenant. Returns None if not stored.

        Does NOT verify that the Keycloak group still exists.
        """
        return cls.objects(is_default=True).first()

    @classmethod
    @trace_fn
    def create_tenant_metadata(
        cls,
        tenant_id: str,
        name: str,
        description: str = "",
        access_rules: list[str] | None = None,
        is_default: bool = False,
    ) -> Self:
        """Stores metadata for an existing Keycloak tenant group.

        The caller is responsible for ensuring the Keycloak group exists first —
        this method only touches the metadata collection.
        """
        tenant = cls(
            id=tenant_id,
            name=name,
            description=description,
            access_rules=access_rules or [],
            is_default=is_default,
        )
        tenant.save()
        return tenant

    @classmethod
    @trace_fn
    def ensure_default_tenant_metadata_exists(
        cls,
        tenant_id: str,
        name: str,
        description: str = "",
        access_rules: list[str] | None = None,
    ) -> Self:
        """
        Ensures default-tenant metadata exists in the collection, creating it if missing.

        Idempotent. Does not create or verify the corresponding Keycloak group.
        """
        existing = cls.get_default_tenant_metadata()
        if existing:
            return existing

        try:
            return cls.create_tenant_metadata(
                tenant_id=tenant_id,
                name=name,
                description=description,
                access_rules=access_rules,
                is_default=True,
            )
        except NotUniqueError:
            existing = cls.get_default_tenant_metadata()
            if existing:
                return existing
            raise

    @classmethod
    @trace_fn
    def update_tenant_metadata(
        cls,
        tenant_id: str,
        name: str | None = None,
        description: str | None = None,
        access_rules: list[str] | None = None,
    ) -> Self | None:
        """
        Updates stored metadata for an existing tenant. Returns the updated entity or None if no metadata was stored.

        Only provided fields are updated. Pass None to skip updating a field.
        Does NOT verify Keycloak group existence — callers that care should check first.
        """
        tenant = cls.get_metadata_by_tenant_id(tenant_id)
        if not tenant:
            return None

        if name is not None:
            tenant.name = name
        if description is not None:
            tenant.description = description
        if access_rules is not None:
            tenant.access_rules = access_rules

        tenant.updated_at = datetime.now(UTC)
        tenant.save()
        return tenant

    @classmethod
    @trace_fn
    def delete_tenant_metadata(cls, tenant_id: str) -> bool:
        """
        Deletes stored metadata for a tenant. Returns True if deleted, False if no metadata was stored.

        Cascades to delete all associated UserTenantRoleEntity and tenant-scoped RoleEntity records.
        Active tenant cleanup in Keycloak must be handled by the caller via
        KeycloakAdminService.clear_active_tenant_for_users_in_tenant().

        Note: ``is_default`` is just a marker for "created at startup" — it carries no
        deletion-protection semantics. Callers that need to prevent leaving the system
        without any tenant should enforce that themselves (e.g., by checking the
        remaining tenant count).

        Uses deferred imports because RoleEntity and UserTenantRoleEntity both import
        this module at module level — importing them here at module level would create circular imports.
        """
        from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
        from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

        tenant = cls.get_metadata_by_tenant_id(tenant_id)
        if not tenant:
            return False

        UserTenantRoleEntity.objects(tenant_id=tenant_id).delete()
        RoleEntity.objects(tenant_id=tenant_id).delete()

        tenant.delete()
        return True
