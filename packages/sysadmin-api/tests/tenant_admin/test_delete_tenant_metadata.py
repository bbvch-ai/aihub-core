# SPDX-License-Identifier: LicenseRef-Proprietary
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_service import TenantAdminService


def _fake_tenant(tenant_id: str = "my-tenant") -> MagicMock:
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.name = "My Tenant"
    tenant.description = "desc"
    tenant.access_rules = ["aihub.admin.>"]
    tenant.created_at = datetime.now(UTC)
    tenant.updated_at = datetime.now(UTC)
    return tenant


def _stub_entity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tenant: MagicMock | None,
    counts: list[int],
    delete_returns: list[bool],
) -> dict[str, MagicMock]:
    """Stubs out all TenantMetadataEntity surface the service uses in delete_tenant_metadata.

    ``counts`` and ``delete_returns`` are consumed in order across calls so a single
    test can simulate the pre-check / post-check race without hand-wiring state.
    """
    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_id", lambda tenant_id: tenant)

    count_iter = iter(counts)
    monkeypatch.setattr(TenantMetadataEntity, "count_tenants", lambda: next(count_iter))

    delete_iter = iter(delete_returns)
    delete_mock = MagicMock(side_effect=lambda tenant_id: next(delete_iter))
    monkeypatch.setattr(TenantMetadataEntity, "delete_tenant_metadata", delete_mock)

    cascade_mock = MagicMock()
    monkeypatch.setattr(TenantMetadataEntity, "cascade_delete_tenant_data", cascade_mock)

    create_mock = MagicMock(return_value=tenant)
    monkeypatch.setattr(TenantMetadataEntity, "create_tenant_metadata", create_mock)

    return {"delete": delete_mock, "cascade": cascade_mock, "create": create_mock}


@pytest.mark.asyncio
async def test_delete_tenant_happy_path_cascades(monkeypatch: pytest.MonkeyPatch) -> None:
    mocks = _stub_entity(
        monkeypatch,
        tenant=_fake_tenant(),
        counts=[2, 1],
        delete_returns=[True],
    )

    await TenantAdminService.delete_tenant_metadata("my-tenant")

    mocks["delete"].assert_called_once_with("my-tenant")
    mocks["cascade"].assert_called_once_with("my-tenant")
    mocks["create"].assert_not_called()


@pytest.mark.asyncio
async def test_delete_tenant_returns_404_when_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    mocks = _stub_entity(monkeypatch, tenant=None, counts=[], delete_returns=[])

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.delete_tenant_metadata("does-not-exist")

    assert exc.value.status_code == 404
    mocks["delete"].assert_not_called()
    mocks["cascade"].assert_not_called()


@pytest.mark.asyncio
async def test_delete_tenant_rejects_when_only_one_tenant_remains(monkeypatch: pytest.MonkeyPatch) -> None:
    mocks = _stub_entity(
        monkeypatch,
        tenant=_fake_tenant(),
        counts=[1],
        delete_returns=[],
    )

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.delete_tenant_metadata("my-tenant")

    assert exc.value.status_code == 409
    assert "last remaining tenant" in exc.value.detail
    mocks["delete"].assert_not_called()
    mocks["cascade"].assert_not_called()
    mocks["create"].assert_not_called()


@pytest.mark.asyncio
async def test_delete_tenant_returns_404_if_concurrently_deleted_between_fetch_and_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pre-check sees the tenant, but by the time we atomically delete it, someone else got there first."""
    mocks = _stub_entity(
        monkeypatch,
        tenant=_fake_tenant(),
        counts=[2],
        delete_returns=[False],
    )

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.delete_tenant_metadata("my-tenant")

    assert exc.value.status_code == 404
    mocks["cascade"].assert_not_called()
    mocks["create"].assert_not_called()


@pytest.mark.asyncio
async def test_delete_tenant_restores_row_and_raises_when_concurrent_delete_took_the_other(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulates: pre-count=2, both sysadmins pass the guard, we delete ours, post-count=0
    because the other delete already ran. We must restore and raise 409 rather than cascade."""
    tenant = _fake_tenant()
    mocks = _stub_entity(
        monkeypatch,
        tenant=tenant,
        counts=[2, 0],
        delete_returns=[True],
    )

    with pytest.raises(HTTPException) as exc:
        await TenantAdminService.delete_tenant_metadata("my-tenant")

    assert exc.value.status_code == 409
    assert "concurrent delete" in exc.value.detail

    mocks["delete"].assert_called_once_with("my-tenant")
    mocks["cascade"].assert_not_called()
    mocks["create"].assert_called_once_with(
        tenant_id="my-tenant",
        name="My Tenant",
        description="desc",
        access_rules=["aihub.admin.>"],
    )


@pytest.mark.asyncio
async def test_delete_tenant_snapshots_before_delete_so_restore_survives_entity_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The snapshot must be a copy, not a live reference — restore should use the pre-delete
    access_rules even if the fetched entity's list object is mutated afterwards."""
    tenant = _fake_tenant()
    tenant.access_rules = ["aihub.admin.>", "aihub.user.>"]
    mocks = _stub_entity(
        monkeypatch,
        tenant=tenant,
        counts=[2, 0],
        delete_returns=[True],
    )

    def mutate_access_rules_on_delete(tenant_id: str) -> bool:
        tenant.access_rules.clear()
        return True

    monkeypatch.setattr(TenantMetadataEntity, "delete_tenant_metadata", mutate_access_rules_on_delete)

    with pytest.raises(HTTPException):
        await TenantAdminService.delete_tenant_metadata("my-tenant")

    mocks["create"].assert_called_once()
    restored_rules = mocks["create"].call_args.kwargs["access_rules"]
    assert restored_rules == ["aihub.admin.>", "aihub.user.>"]
