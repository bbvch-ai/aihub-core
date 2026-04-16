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
        return cls.objects(id=tenant_id).first()

    @classmethod
    @trace_fn
    def get_metadata_by_tenant_name(cls, name: str) -> Self | None:
        return cls.objects(name=name).first()

    @classmethod
    @trace_fn
    def count_tenants(cls) -> int:
        """Returns the number of stored tenant metadata rows. Kept as a dedicated
        method so the last-tenant guard in the tenant-delete flow has a stable,
        mockable seam instead of inlining ``cls.objects.count()``."""
        return cls.objects.count()

    @classmethod
    @trace_fn
    def get_default_tenant_metadata(cls) -> Self | None:
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
        """Atomically deletes the metadata row. Returns True if a row was removed, False otherwise.

        Does NOT cascade to ``RoleEntity`` / ``UserTenantRoleEntity``; call
        ``cascade_delete_tenant_data`` separately once the caller has verified that
        deletion does not violate higher-level invariants (e.g. "at least one tenant
        must remain"). Splitting row-delete from cascade lets the caller undo a
        metadata delete by re-creating the row, which would otherwise be impossible
        once dependent rows are gone.

        Note: ``is_default`` is just a marker for "created at startup" — it carries no
        deletion-protection semantics.
        """
        return cls.objects(id=tenant_id).delete() > 0

    @classmethod
    @trace_fn
    def cascade_delete_tenant_data(cls, tenant_id: str) -> None:
        """Deletes the tenant-scoped role and membership rows.

        Must run only after ``delete_tenant_metadata`` has confirmed the row-delete
        does not violate the last-tenant invariant — this cascade is irreversible
        and would block the restore path. Keycloak-side cleanup (``active_tenant_id``
        attribute) is the caller's responsibility.
        """
        # Deferred: RoleEntity / UserTenantRoleEntity import this module at top level.
        from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
        from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

        UserTenantRoleEntity.objects(tenant_id=tenant_id).delete()
        RoleEntity.objects(tenant_id=tenant_id).delete()
