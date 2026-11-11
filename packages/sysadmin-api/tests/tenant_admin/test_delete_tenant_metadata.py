from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_service import TenantAdminService


def _fake_tenant(tenant_id: str = "my-tenant") -> dict[str, Any]:
    return {
        "_id": tenant_id,
        "name": "My Tenant",
        "description": "desc",
        "access_rules": ["aihub.admin.>"],
        "chat_disclaimer": {"en": "Verify answers."},
        "lcdm_tenant_id": 5,
        "openwebui_mods_json": '{"version":3,"mods":[]}',
        "created_at": datetime(2024, 1, 2, tzinfo=UTC),
        "updated_at": datetime(2025, 3, 4, tzinfo=UTC),
        "unmodeled_settings": {"nested": ["preserve"]},
    }


def _stub_entity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tenant: dict[str, Any] | None,
    counts: list[int],
    delete_returns: list[bool],
) -> dict[str, MagicMock]:
    """Stubs out all TenantMetadataEntity surface the service uses in delete_tenant_metadata.

    ``counts`` and ``delete_returns`` are consumed in order across calls so a single
    test can simulate the pre-check / post-check race without hand-wiring state.
    """
    monkeypatch.setattr(TenantMetadataEntity, "snapshot_tenant_metadata", lambda tenant_id: deepcopy(tenant))

    count_iter = iter(counts)
    monkeypatch.setattr(TenantMetadataEntity, "count_tenants", lambda: next(count_iter))

    delete_iter = iter(delete_returns)
    delete_mock = MagicMock(side_effect=lambda tenant_id: next(delete_iter))
    monkeypatch.setattr(TenantMetadataEntity, "delete_tenant_metadata", delete_mock)

    cascade_mock = MagicMock()
    monkeypatch.setattr(TenantMetadataEntity, "cascade_delete_tenant_data", cascade_mock)

    restore_mock = MagicMock(return_value=tenant)
    monkeypatch.setattr(TenantMetadataEntity, "restore_tenant_metadata", restore_mock)

    return {"delete": delete_mock, "cascade": cascade_mock, "restore": restore_mock}


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
    mocks["restore"].assert_not_called()


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
    mocks["restore"].assert_not_called()


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
    mocks["restore"].assert_not_called()


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
    mocks["restore"].assert_called_once_with(tenant)


@pytest.mark.asyncio
async def test_delete_tenant_snapshots_before_delete_so_restore_survives_entity_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The snapshot must be a copy, not a live reference — restore should use the pre-delete
    access_rules even if the fetched entity's list object is mutated afterwards."""
    tenant = _fake_tenant()
    tenant["access_rules"] = ["aihub.admin.>", "aihub.user.>"]
    mocks = _stub_entity(
        monkeypatch,
        tenant=tenant,
        counts=[2, 0],
        delete_returns=[True],
    )

    def mutate_access_rules_on_delete(tenant_id: str) -> bool:
        tenant["access_rules"].clear()
        tenant["chat_disclaimer"]["en"] = "Changed after deletion"
        tenant["openwebui_mods_json"] = '{"version":4,"mods":[]}'
        tenant["lcdm_tenant_id"] = 6
        return True

    monkeypatch.setattr(TenantMetadataEntity, "delete_tenant_metadata", mutate_access_rules_on_delete)

    with pytest.raises(HTTPException):
        await TenantAdminService.delete_tenant_metadata("my-tenant")

    mocks["restore"].assert_called_once()
    restored = mocks["restore"].call_args.args[0]
    restored_rules = restored["access_rules"]
    assert restored_rules == ["aihub.admin.>", "aihub.user.>"]
    assert restored["openwebui_mods_json"] == '{"version":3,"mods":[]}'
    assert restored["lcdm_tenant_id"] == 5
    assert restored["chat_disclaimer"] == {"en": "Verify answers."}
