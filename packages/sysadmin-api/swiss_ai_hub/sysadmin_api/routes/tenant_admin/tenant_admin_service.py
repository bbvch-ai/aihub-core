from fastapi import HTTPException
from keycloak import KeycloakGetError
from swiss_ai_hub.api.runners.lifetime.initialize_db import initialize_default_roles_for_tenant
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.create_tenant_metadata_request import CreateTenantMetadataRequest
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.tenant_response import TenantResponse
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.tenant_state import TenantState
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.update_tenant_metadata_request import UpdateTenantMetadataRequest

_TENANT_NOT_FOUND = "Tenant not found."


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
            raise HTTPException(status_code=404, detail=_TENANT_NOT_FOUND)

        try:
            await KeycloakAdminService.get_tenant_group(tenant_id)
            state = TenantState.ACTIVE
        except KeycloakGetError:
            state = TenantState.ORPHANED

        return TenantResponse.from_entity(entity, state=state)

    @staticmethod
    @trace_fn
    async def create_tenant_metadata(data: CreateTenantMetadataRequest) -> TenantResponse:
        """Attaches metadata to an existing Keycloak tenant group.

        Ordering invariant: validation runs first, then the idempotent side effects
        (role seeding, superuser membership), and the metadata row is written last.
        On any failure the tenant stays Unconfigured — a retry re-enters here and
        completes cleanly because the side effects are idempotent. This keeps the
        three-state invariant (Active / Orphaned / Unconfigured) intact; a
        partially-configured state is not reachable.
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
            access_rules=[AccessChecker.normalize_model_access_rule(rule) for rule in data.access_rules],
        )
        return TenantResponse.from_entity(entity, state=TenantState.ACTIVE)

    @staticmethod
    @trace_fn
    async def update_tenant_metadata(tenant_id: str, data: UpdateTenantMetadataRequest) -> TenantResponse:
        """Updates MongoDB metadata for an active tenant.

        Orphaned tenants are read-only (409). ``KeycloakGetError`` signals the orphan.
        """
        existing = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not existing:
            raise HTTPException(status_code=404, detail=_TENANT_NOT_FOUND)

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
            access_rules=(
                [AccessChecker.normalize_model_access_rule(rule) for rule in data.access_rules]
                if data.access_rules is not None
                else None
            ),
        )
        if not entity:
            raise HTTPException(status_code=404, detail=_TENANT_NOT_FOUND)
        return TenantResponse.from_entity(entity, state=TenantState.ACTIVE)

    @staticmethod
    @trace_fn
    async def delete_tenant_metadata(tenant_id: str) -> None:
        """Removes the MongoDB metadata. Allowed on both ACTIVE and ORPHANED tenants.

        The Keycloak group (if present) is left untouched — cleanup is managed via
        the Keycloak admin console. The last remaining tenant cannot be deleted,
        otherwise the platform would end up with zero tenants and no user could do
        anything.

        Race-safety: a naive count-then-delete races under concurrent deletes (two
        sysadmins each see ``count == 2``, both proceed, platform ends up empty).
        We snapshot, atomic-delete, re-count, restore the row on a post-violation,
        and only cascade once the invariant is confirmed. The cascade is deferred
        past the re-count because it is irreversible, and the restore would
        otherwise be impossible. The invariant ``count >= 1`` holds after all
        concurrent deletes resolve.
        """
        tenant = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail=_TENANT_NOT_FOUND)

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
        }

        if not TenantMetadataEntity.delete_tenant_metadata(tenant_id):
            raise HTTPException(status_code=404, detail=_TENANT_NOT_FOUND)

        if TenantMetadataEntity.count_tenants() == 0:
            TenantMetadataEntity.create_tenant_metadata(**snapshot)
            raise HTTPException(
                status_code=409,
                detail="Cannot delete the last remaining tenant; a concurrent delete already removed the other.",
            )

        TenantMetadataEntity.cascade_delete_tenant_data(tenant_id)
