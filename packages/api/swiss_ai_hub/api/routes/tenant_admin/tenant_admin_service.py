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
        and 409 if metadata is already present.
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

        entity = TenantMetadataEntity.create_tenant_metadata(
            tenant_id=data.tenant_id,
            name=data.name,
            description=data.description,
            access_rules=data.access_rules,
        )
        await initialize_default_roles_for_tenant(str(entity.id))
        await KeycloakAdminService.assign_superuser_to_tenant(data.tenant_id)
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
    def delete_tenant(tenant_id: str) -> None:
        """Removes the MongoDB metadata. Allowed on both ACTIVE and ORPHANED tenants.

        The Keycloak group (if present) is left untouched — cleanup is a separate
        concern managed via the Keycloak admin console. The last remaining tenant
        cannot be deleted (409) — that would leave the platform with no tenant at
        all and prevent any user from doing anything.
        """
        if TenantMetadataEntity.objects.count() <= 1:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete the last remaining tenant; the platform must always have at least one.",
            )
        deleted = TenantMetadataEntity.delete_tenant_metadata(tenant_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Tenant not found.")
