from fastapi import HTTPException
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity

from swiss_ai_hub.api.routes.tenant_admin.dto.create_tenant_request import CreateTenantRequest
from swiss_ai_hub.api.routes.tenant_admin.dto.tenant_response import TenantResponse
from swiss_ai_hub.api.routes.tenant_admin.dto.update_tenant_request import UpdateTenantRequest


class TenantAdminService:
    """Handles tenant CRUD operations for system administrators."""

    @staticmethod
    @trace_fn
    def list_tenants() -> list[TenantResponse]:
        """Lists all tenants in the system."""
        return [TenantResponse.from_entity(t) for t in TenantEntity.objects.all()]

    @staticmethod
    @trace_fn
    def get_tenant(tenant_id: str) -> TenantResponse:
        """Retrieves a single tenant by its ID."""
        entity = TenantEntity.get_tenant_by_id(tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant not found.")
        return TenantResponse.from_entity(entity)

    @staticmethod
    @trace_fn
    def create_tenant(data: CreateTenantRequest) -> TenantResponse:
        """Creates a new tenant."""
        entity = TenantEntity.create_tenant(
            name=data.name,
            description=data.description,
            access_rules=data.access_rules,
        )
        return TenantResponse.from_entity(entity)

    @staticmethod
    @trace_fn
    def update_tenant(tenant_id: str, data: UpdateTenantRequest) -> TenantResponse:
        """Updates an existing tenant's fields."""
        entity = TenantEntity.update_tenant(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            access_rules=data.access_rules,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant not found.")
        return TenantResponse.from_entity(entity)

    @staticmethod
    @trace_fn
    def delete_tenant(tenant_id: str) -> None:
        """Deletes a tenant. The default tenant cannot be deleted."""
        try:
            deleted = TenantEntity.delete_tenant(tenant_id)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))
        if not deleted:
            raise HTTPException(status_code=404, detail="Tenant not found.")
