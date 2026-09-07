from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.create_tenant_metadata_request import CreateTenantMetadataRequest
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_service import TenantAdminService

INIT_ROLES_PATH = (
    "swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_service.initialize_default_roles_for_tenant"
)


def _stub_metadata_lookups(monkeypatch: pytest.MonkeyPatch, by_id=None, by_name=None) -> None:
    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_id", lambda tenant_id: by_id)
    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_name", lambda name: by_name)


def _fake_entity() -> MagicMock:
    entity = MagicMock()
    entity.id = "my-tenant"
    entity.name = "My Tenant"
    entity.description = "desc"
    entity.access_rules = []
    entity.lcdm_tenant_id = 5
    entity.created_at = datetime.now(UTC)
    entity.updated_at = datetime.now(UTC)
    return entity


def _make_request(lcdm_tenant_id: int | None = None) -> CreateTenantMetadataRequest:
    return CreateTenantMetadataRequest(
        tenant_id="my-tenant",
        name="My Tenant",
        description="desc",
        access_rules=[],
        lcdm_tenant_id=lcdm_tenant_id,
    )


@pytest.mark.asyncio
async def test_provision_new_tenant_creates_group_then_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """A brand-new tenant: the Keycloak group is created (idempotent) and metadata is created."""
    _stub_metadata_lookups(monkeypatch)  # neither id nor name exists
    create_group = AsyncMock(return_value="kc-group-id")
    monkeypatch.setattr(KeycloakAdminService, "create_tenant_group", create_group)
    monkeypatch.setattr(INIT_ROLES_PATH, AsyncMock(return_value=None))
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", AsyncMock(return_value=None))

    create_mock = MagicMock(return_value=_fake_entity())
    update_mock = MagicMock()
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)
    monkeypatch.setattr(TenantMetadataEntity, "update_tenant_metadata", update_mock)

    result = await TenantAdminService.provision_tenant(_make_request())

    create_group.assert_awaited_once_with("my-tenant")
    create_mock.assert_called_once()
    update_mock.assert_not_called()
    assert result.id == "my-tenant"


@pytest.mark.asyncio
async def test_provision_existing_tenant_updates_metadata_idempotently(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-running the sync for an already-configured tenant updates metadata instead of failing (upsert)."""
    _stub_metadata_lookups(monkeypatch, by_id=MagicMock(id="my-tenant"), by_name=MagicMock(id="my-tenant"))
    monkeypatch.setattr(KeycloakAdminService, "create_tenant_group", AsyncMock(return_value=None))
    monkeypatch.setattr(INIT_ROLES_PATH, AsyncMock(return_value=None))
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", AsyncMock(return_value=None))

    create_mock = MagicMock()
    update_mock = MagicMock(return_value=_fake_entity())
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)
    monkeypatch.setattr(TenantMetadataEntity, "update_tenant_metadata", update_mock)

    result = await TenantAdminService.provision_tenant(_make_request())

    update_mock.assert_called_once()
    create_mock.assert_not_called()
    assert result.id == "my-tenant"


@pytest.mark.asyncio
async def test_provision_passes_lcdm_tenant_id_through_on_create(monkeypatch: pytest.MonkeyPatch) -> None:
    """The LCDM tenant id from the request is stored on create so it can be read off the AI Hub tenant."""
    _stub_metadata_lookups(monkeypatch)
    monkeypatch.setattr(KeycloakAdminService, "create_tenant_group", AsyncMock(return_value=None))
    monkeypatch.setattr(INIT_ROLES_PATH, AsyncMock(return_value=None))
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", AsyncMock(return_value=None))

    create_mock = MagicMock(return_value=_fake_entity())
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)
    monkeypatch.setattr(TenantMetadataEntity, "update_tenant_metadata", MagicMock())

    result = await TenantAdminService.provision_tenant(_make_request(lcdm_tenant_id=5))

    assert create_mock.call_args.kwargs["lcdm_tenant_id"] == 5
    assert result.lcdm_tenant_id == 5


@pytest.mark.asyncio
async def test_provision_passes_lcdm_tenant_id_through_on_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-syncing an existing tenant transfers the LCDM id via update, not just on first insert."""
    _stub_metadata_lookups(monkeypatch, by_id=MagicMock(id="my-tenant"), by_name=MagicMock(id="my-tenant"))
    monkeypatch.setattr(KeycloakAdminService, "create_tenant_group", AsyncMock(return_value=None))
    monkeypatch.setattr(INIT_ROLES_PATH, AsyncMock(return_value=None))
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", AsyncMock(return_value=None))

    update_mock = MagicMock(return_value=_fake_entity())
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", MagicMock())
    monkeypatch.setattr(TenantMetadataEntity, "update_tenant_metadata", update_mock)

    await TenantAdminService.provision_tenant(_make_request(lcdm_tenant_id=5))

    assert update_mock.call_args.kwargs["lcdm_tenant_id"] == 5


@pytest.mark.asyncio
async def test_provision_rejects_name_taken_by_other_tenant_before_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The name belongs to a different tenant id → 409, and no group/side effects run."""
    _stub_metadata_lookups(monkeypatch, by_name=MagicMock(id="other-tenant", name="My Tenant"))
    create_group = AsyncMock()
    roles_mock = AsyncMock()
    superuser_mock = AsyncMock()
    monkeypatch.setattr(KeycloakAdminService, "create_tenant_group", create_group)
    monkeypatch.setattr(INIT_ROLES_PATH, roles_mock)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", superuser_mock)

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.provision_tenant(_make_request())

    assert exc.value.status_code == 409
    create_group.assert_not_awaited()
    roles_mock.assert_not_awaited()
    superuser_mock.assert_not_awaited()
