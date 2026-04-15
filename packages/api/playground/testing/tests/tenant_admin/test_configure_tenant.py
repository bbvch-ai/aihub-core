from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.keycloak.models.keycloak_group import KeycloakGroup
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.api.routes.tenant_admin.dto.configure_tenant_request import ConfigureTenantRequest
from swiss_ai_hub.api.routes.tenant_admin.tenant_admin_service import TenantAdminService


@pytest.mark.asyncio
async def test_configure_tenant_assigns_superuser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        KeycloakAdminService,
        "get_tenant_group",
        AsyncMock(return_value=KeycloakGroup(id="kc-group-id", name="my-tenant")),
    )

    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_id", lambda tenant_id: None)

    fake_entity = MagicMock()
    fake_entity.id = "my-tenant"
    fake_entity.name = "My Tenant"
    fake_entity.description = "desc"
    fake_entity.access_rules = []
    fake_entity.is_default = False
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", lambda **_kwargs: fake_entity)

    monkeypatch.setattr(
        "swiss_ai_hub.api.routes.tenant_admin.tenant_admin_service.initialize_default_roles_for_tenant",
        AsyncMock(return_value=None),
    )

    mock_assign_superuser = AsyncMock(return_value=None)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", mock_assign_superuser)

    request = ConfigureTenantRequest(
        tenant_id="my-tenant",
        name="My Tenant",
        description="desc",
        access_rules=[],
    )
    await TenantAdminService.configure_tenant(request)

    mock_assign_superuser.assert_awaited_once_with("my-tenant")
