from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from keycloak import KeycloakGetError
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.keycloak.models.keycloak_group import KeycloakGroup
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.api.routes.tenant_admin.dto.configure_tenant_request import ConfigureTenantRequest
from swiss_ai_hub.api.routes.tenant_admin.tenant_admin_service import TenantAdminService

INIT_ROLES_PATH = "swiss_ai_hub.api.routes.tenant_admin.tenant_admin_service.initialize_default_roles_for_tenant"


def _stub_metadata_lookups(monkeypatch: pytest.MonkeyPatch, by_id=None, by_name=None) -> None:
    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_id", lambda tenant_id: by_id)
    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_name", lambda name: by_name)


def _stub_keycloak_group_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        KeycloakAdminService,
        "get_tenant_group",
        AsyncMock(return_value=KeycloakGroup(id="kc-group-id", name="my-tenant")),
    )


def _make_request() -> ConfigureTenantRequest:
    return ConfigureTenantRequest(
        tenant_id="my-tenant",
        name="My Tenant",
        description="desc",
        access_rules=[],
    )


@pytest.mark.asyncio
async def test_configure_tenant_persists_metadata_last(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path — side effects run before metadata is persisted."""
    _stub_keycloak_group_exists(monkeypatch)
    _stub_metadata_lookups(monkeypatch)

    call_order: list[str] = []
    fake_entity = MagicMock()
    fake_entity.id = "my-tenant"
    fake_entity.name = "My Tenant"
    fake_entity.description = "desc"
    fake_entity.access_rules = []
    fake_entity.is_default = False
    fake_entity.created_at = datetime.now(UTC)
    fake_entity.updated_at = datetime.now(UTC)

    async def record_roles(tenant_id: str) -> None:
        call_order.append("roles")

    async def record_superuser(tenant_id: str) -> None:
        call_order.append("superuser")

    def record_create(**_kwargs) -> MagicMock:
        call_order.append("metadata")
        return fake_entity

    monkeypatch.setattr(INIT_ROLES_PATH, record_roles)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", record_superuser)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", record_create)

    await TenantAdminService.configure_tenant(_make_request())

    assert call_order == ["roles", "superuser", "metadata"]


@pytest.mark.asyncio
async def test_configure_tenant_rejects_missing_keycloak_group_before_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        KeycloakAdminService,
        "get_tenant_group",
        AsyncMock(side_effect=KeycloakGetError("missing")),
    )
    _stub_metadata_lookups(monkeypatch)

    roles_mock = AsyncMock()
    superuser_mock = AsyncMock()
    create_mock = MagicMock()
    monkeypatch.setattr(INIT_ROLES_PATH, roles_mock)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", superuser_mock)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.configure_tenant(_make_request())

    assert exc.value.status_code == 400
    roles_mock.assert_not_awaited()
    superuser_mock.assert_not_awaited()
    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_configure_tenant_rejects_existing_tenant_id_before_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_keycloak_group_exists(monkeypatch)
    _stub_metadata_lookups(monkeypatch, by_id=MagicMock(id="my-tenant"))

    roles_mock = AsyncMock()
    superuser_mock = AsyncMock()
    create_mock = MagicMock()
    monkeypatch.setattr(INIT_ROLES_PATH, roles_mock)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", superuser_mock)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.configure_tenant(_make_request())

    assert exc.value.status_code == 409
    roles_mock.assert_not_awaited()
    superuser_mock.assert_not_awaited()
    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_configure_tenant_rejects_taken_name_before_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_keycloak_group_exists(monkeypatch)
    _stub_metadata_lookups(monkeypatch, by_name=MagicMock(id="other-tenant", name="My Tenant"))

    roles_mock = AsyncMock()
    superuser_mock = AsyncMock()
    create_mock = MagicMock()
    monkeypatch.setattr(INIT_ROLES_PATH, roles_mock)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", superuser_mock)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.configure_tenant(_make_request())

    assert exc.value.status_code == 409
    roles_mock.assert_not_awaited()
    superuser_mock.assert_not_awaited()
    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_configure_tenant_does_not_persist_metadata_if_role_seeding_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If role seeding raises, metadata must not be persisted — retry can recover."""
    _stub_keycloak_group_exists(monkeypatch)
    _stub_metadata_lookups(monkeypatch)

    monkeypatch.setattr(INIT_ROLES_PATH, AsyncMock(side_effect=RuntimeError("role seeding down")))
    superuser_mock = AsyncMock()
    create_mock = MagicMock()
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", superuser_mock)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)

    with pytest.raises(RuntimeError):
        await TenantAdminService.configure_tenant(_make_request())

    superuser_mock.assert_not_awaited()
    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_configure_tenant_does_not_persist_metadata_if_superuser_assignment_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If superuser assignment raises, metadata must not be persisted — role seeding is idempotent on retry."""
    _stub_keycloak_group_exists(monkeypatch)
    _stub_metadata_lookups(monkeypatch)

    monkeypatch.setattr(INIT_ROLES_PATH, AsyncMock(return_value=None))
    monkeypatch.setattr(
        KeycloakAdminService,
        "assign_superuser_to_tenant",
        AsyncMock(side_effect=RuntimeError("keycloak down")),
    )
    create_mock = MagicMock()
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)

    with pytest.raises(RuntimeError):
        await TenantAdminService.configure_tenant(_make_request())

    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_configure_tenant_retry_after_midflight_failure_completes_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The load-bearing three-state invariant: if ``assign_superuser_to_tenant`` raises on
    attempt #1, the metadata row must not be written, leaving the tenant Unconfigured.
    A retry (attempt #2) must then complete with exactly one metadata write and exactly
    one role-seed pass's worth of roles. Role seeding runs on both attempts because it is
    documented as idempotent — this test pins that contract.
    """
    _stub_keycloak_group_exists(monkeypatch)
    _stub_metadata_lookups(monkeypatch)

    role_calls: list[str] = []
    superuser_calls: list[str] = []
    create_calls: list[dict] = []

    async def record_roles(tenant_id: str) -> None:
        role_calls.append(tenant_id)

    superuser_side_effects = iter([RuntimeError("keycloak flake"), None])

    async def flaky_superuser(tenant_id: str) -> None:
        superuser_calls.append(tenant_id)
        outcome = next(superuser_side_effects)
        if isinstance(outcome, Exception):
            raise outcome

    fake_entity = MagicMock()
    fake_entity.id = "my-tenant"
    fake_entity.name = "My Tenant"
    fake_entity.description = "desc"
    fake_entity.access_rules = []
    fake_entity.is_default = False
    fake_entity.created_at = datetime.now(UTC)
    fake_entity.updated_at = datetime.now(UTC)

    def record_create(**kwargs) -> MagicMock:
        create_calls.append(kwargs)
        return fake_entity

    monkeypatch.setattr(INIT_ROLES_PATH, record_roles)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", flaky_superuser)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", record_create)

    with pytest.raises(RuntimeError, match="keycloak flake"):
        await TenantAdminService.configure_tenant(_make_request())

    assert role_calls == ["my-tenant"], "role seed must have run once before the superuser step"
    assert superuser_calls == ["my-tenant"], "superuser assignment must have been attempted"
    assert create_calls == [], "metadata must not be persisted when a prior side effect failed"

    await TenantAdminService.configure_tenant(_make_request())

    assert role_calls == ["my-tenant", "my-tenant"], "role seed must run on the retry too (contract: idempotent)"
    assert superuser_calls == ["my-tenant", "my-tenant"], "superuser assignment must be retried"
    assert len(create_calls) == 1, "retry must produce exactly one metadata row"


@pytest.mark.asyncio
async def test_configure_tenant_assigns_superuser(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_keycloak_group_exists(monkeypatch)
    _stub_metadata_lookups(monkeypatch)

    fake_entity = MagicMock()
    fake_entity.id = "my-tenant"
    fake_entity.name = "My Tenant"
    fake_entity.description = "desc"
    fake_entity.access_rules = []
    fake_entity.is_default = False
    fake_entity.created_at = datetime.now(UTC)
    fake_entity.updated_at = datetime.now(UTC)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", lambda **_kwargs: fake_entity)
    monkeypatch.setattr(INIT_ROLES_PATH, AsyncMock(return_value=None))

    mock_assign_superuser = AsyncMock(return_value=None)
    monkeypatch.setattr(KeycloakAdminService, "assign_superuser_to_tenant", mock_assign_superuser)

    await TenantAdminService.configure_tenant(_make_request())

    mock_assign_superuser.assert_awaited_once_with("my-tenant")
