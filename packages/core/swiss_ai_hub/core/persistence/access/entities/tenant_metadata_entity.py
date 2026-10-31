from datetime import UTC, datetime
from typing import Self

from beanie import Delete, Document, Insert, Replace, Save, SaveChanges, after_event
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, IndexModel
from pymongo.errors import DuplicateKeyError

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook


class TenantMetadataEntity(Document):
    """
    Metadata (display name, description, access rules, chat disclaimer) for a tenant.

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

    Unknown fields are kept (`extra="allow"`): the MongoEngine document ran `strict: False`.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str = ""
    access_rules: list[str] = Field(default_factory=list)
    chat_disclaimer: LocaleString | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "tenants"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [IndexModel([("name", ASCENDING)], unique=True)]

    @after_event(Insert, Replace, Save, SaveChanges, Delete)
    def _resync_openwebui_access(self) -> None:
        AccessChangeHook.notify()

    @classmethod
    @trace_fn
    async def get_metadata_by_tenant_id(cls, tenant_id: str) -> Self | None:
        return await cls.get(tenant_id)

    @classmethod
    @trace_fn
    async def get_metadata_by_tenant_name(cls, name: str) -> Self | None:
        return await cls.find_one({"name": name})

    @classmethod
    @trace_fn
    async def get_all_metadata(cls) -> list[Self]:
        return await cls.find().to_list()

    @classmethod
    @trace_fn
    async def get_metadata_for_tenant_ids(cls, tenant_ids: list[str]) -> list[Self]:
        return await cls.find({"_id": {"$in": tenant_ids}}).to_list()

    @classmethod
    @trace_fn
    async def get_earliest_created(cls, tenant_ids: list[str]) -> Self | None:
        """The metadata created first among these tenants; None if none of them has metadata."""
        return await cls.find({"_id": {"$in": tenant_ids}}).sort("created_at").first_or_none()

    @classmethod
    @trace_fn
    async def count_tenants(cls) -> int:
        """Returns the number of stored tenant metadata rows. Kept as a dedicated
        method so the last-tenant guard in the tenant-delete flow has a stable,
        mockable seam."""
        return await cls.find().count()

    @classmethod
    @trace_fn
    async def get_startup_tenant_metadata(cls) -> Self | None:
        """Metadata for the tenant seeded at platform startup, looked up by its
        configured id. There is no database flag — the "startup tenant" is simply
        the one whose id matches ``StartupTenantSettings().ID``."""
        # Deferred: StartupTenantSettings lives under core.infrastructure and
        # importing it at module load time would cycle through settings bootstrap.
        from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings

        return await cls.get_metadata_by_tenant_id(StartupTenantSettings().ID)

    @classmethod
    @trace_fn
    async def create_tenant_metadata(
        cls,
        tenant_id: str,
        name: str,
        description: str = "",
        access_rules: list[str] | None = None,
        chat_disclaimer: LocaleString | None = None,
    ) -> Self:
        """Stores metadata for an existing Keycloak tenant group.

        The caller is responsible for ensuring the Keycloak group exists first —
        this method only touches the metadata collection. Raises pymongo's `DuplicateKeyError` for a taken id or name.
        """
        tenant = cls(
            id=tenant_id,
            name=name,
            description=description,
            access_rules=access_rules or [],
            chat_disclaimer=chat_disclaimer,
        )
        return await tenant.insert()

    @classmethod
    @trace_fn
    async def ensure_startup_tenant_metadata_exists(
        cls,
        tenant_id: str,
        name: str,
        description: str = "",
        access_rules: list[str] | None = None,
    ) -> Self:
        """Ensures the startup tenant's metadata row exists. Idempotent.

        Does not create or verify the corresponding Keycloak group.
        """
        existing = await cls.get_metadata_by_tenant_id(tenant_id)
        if existing:
            return existing

        try:
            return await cls.create_tenant_metadata(
                tenant_id=tenant_id,
                name=name,
                description=description,
                access_rules=access_rules,
            )
        except DuplicateKeyError:
            existing = await cls.get_metadata_by_tenant_id(tenant_id)
            if existing:
                return existing
            raise

    @classmethod
    @trace_fn
    async def update_tenant_metadata(
        cls,
        tenant_id: str,
        name: str | None = None,
        description: str | None = None,
        access_rules: list[str] | None = None,
        chat_disclaimer: LocaleString | None = None,
    ) -> Self | None:
        """
        Updates stored metadata for an existing tenant. Returns the updated entity or None if no metadata was stored.

        Only provided fields are updated. Pass None to skip updating a field.
        Does NOT verify Keycloak group existence — callers that care should check first.
        """
        tenant = await cls.get_metadata_by_tenant_id(tenant_id)
        if not tenant:
            return None

        if name is not None:
            tenant.name = name
        if description is not None:
            tenant.description = description
        if access_rules is not None:
            tenant.access_rules = access_rules
        if chat_disclaimer is not None:
            tenant.chat_disclaimer = chat_disclaimer

        tenant.updated_at = datetime.now(UTC)
        await tenant.save_changes()
        return tenant

    @classmethod
    @trace_fn
    async def grant_access_rule(cls, tenant_id: str, access_rule: str) -> Self:
        """Adds a single access rule to a tenant's ceiling. Idempotent.

        Saves through the document (not an atomic update) so its `AccessChangeHook` event fires and OpenWebUI
        access re-syncs. Raises if the tenant has no metadata row, so callers can roll back a dependent operation.
        """
        tenant = await cls.get_metadata_by_tenant_id(tenant_id)
        if not tenant:
            raise ValueError(f"No tenant metadata for '{tenant_id}'; cannot grant access rule.")

        if access_rule not in tenant.access_rules:
            tenant.access_rules = [*tenant.access_rules, access_rule]
            tenant.updated_at = datetime.now(UTC)
            await tenant.save_changes()
        return tenant

    @classmethod
    @trace_fn
    async def revoke_access_rule_from_all_tenants(cls, access_rules: list[str]) -> None:
        """Removes the given access rules from every tenant ceiling that holds any of them.

        Saves per modified row so `AccessChangeHook` re-syncs OpenWebUI.
        """
        rules_to_remove = set(access_rules)
        for tenant in await cls.find({"access_rules": {"$in": list(rules_to_remove)}}).to_list():
            tenant.access_rules = [rule for rule in tenant.access_rules if rule not in rules_to_remove]
            tenant.updated_at = datetime.now(UTC)
            await tenant.save_changes()

    @classmethod
    @trace_fn
    async def delete_tenant_metadata(cls, tenant_id: str) -> bool:
        """Atomically deletes the metadata row. Returns True if a row was removed, False otherwise.

        Does NOT cascade to ``RoleEntity`` / ``UserTenantRoleEntity``; call
        ``cascade_delete_tenant_data`` separately once the caller has verified that
        deletion does not violate higher-level invariants (e.g. "at least one tenant
        must remain"). Splitting row-delete from cascade lets the caller undo a
        metadata delete by re-creating the row, which would otherwise be impossible
        once dependent rows are gone. One query delete, so two concurrent callers cannot both see True; it fires no
        document event, so the OpenWebUI re-sync is asked for here.
        """
        result = await cls.find({"_id": tenant_id}).delete()
        if not result.deleted_count:
            return False
        AccessChangeHook.notify()
        return True

    @classmethod
    @trace_fn
    async def cascade_delete_tenant_data(cls, tenant_id: str) -> None:
        """Deletes tenant settings, roles and memberships.

        Must run only after ``delete_tenant_metadata`` has confirmed the row-delete
        does not violate the last-tenant invariant — this cascade is irreversible
        and would block the restore path. Keycloak-side cleanup (``active_tenant_id``
        attribute) is the caller's responsibility.
        """
        # Deferred: RoleEntity / UserTenantRoleEntity import this module at top level.
        from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
        from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

        await UserTenantRoleEntity.delete_memberships_of_tenant(tenant_id)
        await RoleEntity.delete_roles_of_tenant(tenant_id)
