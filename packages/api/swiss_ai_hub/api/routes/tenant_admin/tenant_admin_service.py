from fastapi import HTTPException
from keycloak import KeycloakGetError
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.api.routes.tenant_admin.dto.configure_tenant_request import ConfigureTenantRequest
from swiss_ai_hub.api.routes.tenant_admin.dto.tenant_response import TenantResponse
from swiss_ai_hub.api.routes.tenant_admin.dto.tenant_state import TenantState
from swiss_ai_hub.api.routes.tenant_admin.dto.update_tenant_request import UpdateTenantRequest
from swiss_ai_hub.api.runners.lifetime.initialize_db import initialize_default_roles_for_tenant


class TenantAdminService:
    """Handles tenant CRUD operations for system administrators.

    Tenants live in two places: Keycloak (group under ``/tenants/``) owns existence
    and user membership; MongoDB ``TenantMetadataEntity`` owns display metadata
    (name, description, access rules). A tenant is only accessible to end users
    when it exists in both. Sysadmins can see orphaned metadata (MongoDB only)
    and delete it, but cannot edit it.
    """

    @staticmethod
    @trace_fn
    async def list_tenants() -> list[TenantResponse]:
        """Active tenants (both sources) + orphaned tenants (Mongo-only) for the sysadmin view.

        Keycloak-only IDs (unconfigured) are served by ``list_unconfigured_tenant_ids``.
        """
        keycloak_groups = await KeycloakAdminService.get_all_tenant_groups()
        keycloak_ids = {g.name for g in keycloak_groups}
        result: list[TenantResponse] = []
        for entity in TenantMetadataEntity.objects.all():
            state = TenantState.ACTIVE if entity.id in keycloak_ids else TenantState.ORPHANED
            result.append(TenantResponse.from_entity(entity, state=state))
        return result

    @staticmethod
    @trace_fn
    async def list_unconfigured_tenant_ids() -> list[str]:
        """Keycloak tenant IDs that don't yet have MongoDB metadata."""
        keycloak_groups = await KeycloakAdminService.get_all_tenant_groups()
        keycloak_ids = {g.name for g in keycloak_groups}
        configured_ids = {t.id for t in TenantMetadataEntity.objects.only("id")}
        return sorted(keycloak_ids - configured_ids)

    @staticmethod
    @trace_fn
    async def get_tenant(tenant_id: str) -> TenantResponse:
        """Retrieves a single tenant and its state.

        ``KeycloakGetError`` is used here as control flow: its absence means the group
        exists (ACTIVE), its presence means the group is gone (ORPHANED).
        """
        entity = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant not found.")

        try:
            await KeycloakAdminService.get_tenant_group(tenant_id)
            state = TenantState.ACTIVE
        except KeycloakGetError:
            state = TenantState.ORPHANED

        return TenantResponse.from_entity(entity, state=state)

    @staticmethod
    @trace_fn
    async def configure_tenant(data: ConfigureTenantRequest) -> TenantResponse:
        """Attaches metadata to an existing Keycloak tenant group.

        Raises 400 if the Keycloak group does not exist (we use ``KeycloakGetError``
        as control flow — its presence means the Keycloak side does not have this id),
        and 409 if metadata is already present for this ``tenant_id`` or the display
        ``name`` is taken.

        Ordering invariant: all validation runs before any side effects, then both
        idempotent side effects (role seeding, superuser group membership) run
        before the metadata is persisted. The metadata row is the *last* write,
        so any failure along the way leaves the tenant in the Unconfigured state —
        a subsequent retry will re-enter this method and complete cleanly because
        both side effects are idempotent. This preserves the three-state invariant
        (Active / Orphaned / Unconfigured); a partially-configured state is not
        reachable.
        """
        try:
            await KeycloakAdminService.get_tenant_group(data.tenant_id)
        except KeycloakGetError:
            raise HTTPException(
                status_code=400,
                detail=f"Keycloak tenant group '{data.tenant_id}' does not exist.",
            )

        if TenantMetadataEntity.get_metadata_by_tenant_id(data.tenant_id):
            raise HTTPException(
                status_code=409,
                detail=f"Tenant '{data.tenant_id}' is already configured.",
            )

        if TenantMetadataEntity.get_metadata_by_tenant_name(data.name):
            raise HTTPException(
                status_code=409,
                detail=f"Tenant with name '{data.name}' already exists.",
            )

        await initialize_default_roles_for_tenant(data.tenant_id)
        await KeycloakAdminService.assign_superuser_to_tenant(data.tenant_id)

        entity = TenantMetadataEntity.create_tenant_metadata(
            tenant_id=data.tenant_id,
            name=data.name,
            description=data.description,
            access_rules=data.access_rules,
        )
        return TenantResponse.from_entity(entity, state=TenantState.ACTIVE)

    @staticmethod
    @trace_fn
    async def update_tenant(tenant_id: str, data: UpdateTenantRequest) -> TenantResponse:
        """Updates MongoDB metadata for an active tenant.

        Orphaned tenants are read-only (409). ``KeycloakGetError`` signals the orphan.
        """
        existing = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Tenant not found.")

        try:
            await KeycloakAdminService.get_tenant_group(tenant_id)
        except KeycloakGetError:
            raise HTTPException(
                status_code=409,
                detail=f"Tenant '{tenant_id}' is orphaned (Keycloak group missing) and cannot be edited.",
            )

        entity = TenantMetadataEntity.update_tenant_metadata(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            access_rules=data.access_rules,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant not found.")
        return TenantResponse.from_entity(entity, state=TenantState.ACTIVE)

    @staticmethod
    @trace_fn
    async def delete_tenant(tenant_id: str) -> None:
        """Removes the MongoDB metadata. Allowed on both ACTIVE and ORPHANED tenants.

        The Keycloak group (if present) is left untouched — cleanup is a separate
        concern managed via the Keycloak admin console. The last remaining tenant
        cannot be deleted (409) — that would leave the platform with no tenant at
        all and prevent any user from doing anything.

        Race-safety: a naive ``count() <= 1`` pre-check is racy under concurrent
        deletes (two sysadmins could each see ``count == 2`` and both proceed,
        leaving the platform with zero tenants). The sequence here closes that gap
        without requiring distributed locks or MongoDB transactions:

        1. Preliminary count check — fast-fails the obvious case.
        2. Snapshot the metadata (so we can undo).
        3. Atomic single-document delete.
        4. Re-count. If zero tenants remain, a concurrent delete took the other
           one; restore the row we just deleted and raise 409. The restore is
           itself atomic on a single document.
        5. Only after the invariant is confirmed do we cascade the role/
           membership cleanup — these cascades are irreversible, so deferring
           them past the post-condition check is what makes the restore viable.

        In any interleaving of concurrent deletes, either exactly one delete wins
        and the rest get 409 (when one-of-two races), or all get 409 and every row
        is restored (when both-of-two race). The invariant ``count >= 1`` holds
        throughout in the steady state after all deletes resolve.
        """
        tenant = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found.")

        if TenantMetadataEntity.count_tenants() <= 1:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete the last remaining tenant; the platform must always have at least one.",
            )

        snapshot = {
            "tenant_id": tenant.id,
            "name": tenant.name,
            "description": tenant.description,
            "access_rules": list(tenant.access_rules),
            "is_default": tenant.is_default,
        }

        if not TenantMetadataEntity.delete_tenant_metadata(tenant_id):
            raise HTTPException(status_code=404, detail="Tenant not found.")

        if TenantMetadataEntity.count_tenants() == 0:
            TenantMetadataEntity.create_tenant_metadata(**snapshot)
            raise HTTPException(
                status_code=409,
                detail="Cannot delete the last remaining tenant; a concurrent delete already removed the other.",
            )

        TenantMetadataEntity.cascade_delete_tenant_data(tenant_id)
