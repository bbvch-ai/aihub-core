import contextlib
import inspect
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakDeleteError, KeycloakGetError

from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.testing.auth_utils.keycloak_utils import create_real_keycloak_admin


@pytest.fixture
def admin() -> KeycloakAdmin:
    return create_real_keycloak_admin()


@pytest_asyncio.fixture
async def seeded_user(admin: KeycloakAdmin) -> AsyncIterator[tuple[str, str]]:
    """Creates a user via the raw admin SDK — independent of the service under test."""
    email = f"itest-{uuid.uuid4().hex[:8]}@example.com"
    user_id = await admin.a_create_user({"email": email, "username": email, "enabled": True})
    yield user_id, email
    with contextlib.suppress(KeycloakDeleteError, KeycloakGetError):
        await admin.a_delete_user(user_id)


@pytest_asyncio.fixture
async def seeded_tenant_group(admin: KeycloakAdmin) -> AsyncIterator[str]:
    """Creates a tenant group via the raw admin SDK — independent of the service under test."""
    tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"
    parent = await admin.a_get_group_by_path("/tenants")
    await admin.a_create_group({"name": tenant_id}, parent=parent["id"])
    yield tenant_id
    with contextlib.suppress(KeycloakDeleteError, KeycloakGetError):
        group = await admin.a_get_group_by_path(f"/tenants/{tenant_id}")
        await admin.a_delete_group(group["id"])


class TestUserCrud:
    @pytest.mark.asyncio
    async def test_create_user(self, admin: KeycloakAdmin) -> None:
        email = f"itest-{uuid.uuid4().hex[:8]}@example.com"
        user_id: str | None = None
        try:
            user_id = await KeycloakAdminService.create_user(email)
            assert user_id is not None

            raw = await admin.a_get_user(user_id)
            assert raw["email"] == email
            assert raw["username"] == email
            assert raw["enabled"] is True
        finally:
            if user_id is not None:
                with contextlib.suppress(KeycloakDeleteError, KeycloakGetError):
                    await admin.a_delete_user(user_id)

    @pytest.mark.asyncio
    async def test_find_user_by_email(self, seeded_user: tuple[str, str]) -> None:
        user_id, email = seeded_user

        found = await KeycloakAdminService.find_user_by_email(email)

        assert found is not None
        assert found.id == user_id
        assert found.email == email

    @pytest.mark.asyncio
    async def test_find_user_by_email_returns_none_when_missing(self) -> None:
        result = await KeycloakAdminService.find_user_by_email(f"itest-missing-{uuid.uuid4().hex[:8]}@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, seeded_user: tuple[str, str]) -> None:
        user_id, email = seeded_user

        user = await KeycloakAdminService.get_user_by_id(user_id)

        assert user.id == user_id
        assert user.email == email

    @pytest.mark.asyncio
    async def test_get_users_by_ids_tolerates_missing(self, seeded_user: tuple[str, str]) -> None:
        user_id, _ = seeded_user
        bogus_id = str(uuid.uuid4())

        result = await KeycloakAdminService.get_users_by_ids([user_id, bogus_id])

        assert user_id in result
        assert bogus_id not in result

    @pytest.mark.asyncio
    async def test_get_all_users_contains_created(self, seeded_user: tuple[str, str]) -> None:
        user_id, _ = seeded_user

        all_users = await KeycloakAdminService.get_all_users(max_results=1000)

        assert any(u.id == user_id for u in all_users)


class TestTenantGroups:
    @pytest.mark.asyncio
    async def test_create_tenant_group(self, admin: KeycloakAdmin) -> None:
        tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"
        try:
            await KeycloakAdminService.create_tenant_group(tenant_id)

            raw = await admin.a_get_group_by_path(f"/tenants/{tenant_id}")
            assert raw["name"] == tenant_id
        finally:
            with contextlib.suppress(KeycloakDeleteError, KeycloakGetError):
                raw = await admin.a_get_group_by_path(f"/tenants/{tenant_id}")
                await admin.a_delete_group(raw["id"])

    @pytest.mark.asyncio
    async def test_get_tenant_group(self, seeded_tenant_group: str) -> None:
        group = await KeycloakAdminService.get_tenant_group(seeded_tenant_group)

        assert group.name == seeded_tenant_group
        assert group.path == f"/tenants/{seeded_tenant_group}"

    @pytest.mark.asyncio
    async def test_assign_and_remove_user_to_tenant(
        self,
        admin: KeycloakAdmin,
        seeded_user: tuple[str, str],
        seeded_tenant_group: str,
    ) -> None:
        user_id, _ = seeded_user

        await KeycloakAdminService.assign_user_to_tenant(user_id, seeded_tenant_group)
        group = await admin.a_get_group_by_path(f"/tenants/{seeded_tenant_group}")
        members = await admin.a_get_group_members(group["id"])
        assert any(m["id"] == user_id for m in members)

        await KeycloakAdminService.remove_user_from_tenant(user_id, seeded_tenant_group)
        members_after = await admin.a_get_group_members(group["id"])
        assert all(m["id"] != user_id for m in members_after)

    @pytest.mark.asyncio
    async def test_get_tenant_members(
        self, admin: KeycloakAdmin, seeded_user: tuple[str, str], seeded_tenant_group: str
    ) -> None:
        user_id, _ = seeded_user
        group = await admin.a_get_group_by_path(f"/tenants/{seeded_tenant_group}")
        await admin.a_group_user_add(user_id, group["id"])

        members = await KeycloakAdminService.get_tenant_members(seeded_tenant_group, offset=0, limit=100)

        assert any(m.id == user_id for m in members)

    @pytest.mark.asyncio
    async def test_count_tenant_members(
        self, admin: KeycloakAdmin, seeded_user: tuple[str, str], seeded_tenant_group: str
    ) -> None:
        user_id, _ = seeded_user

        assert await KeycloakAdminService.count_tenant_members(seeded_tenant_group) == 0

        group = await admin.a_get_group_by_path(f"/tenants/{seeded_tenant_group}")
        await admin.a_group_user_add(user_id, group["id"])

        assert await KeycloakAdminService.count_tenant_members(seeded_tenant_group) == 1

    @pytest.mark.asyncio
    async def test_delete_tenant_group(self, admin: KeycloakAdmin) -> None:
        tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"
        parent = await admin.a_get_group_by_path("/tenants")
        await admin.a_create_group({"name": tenant_id}, parent=parent["id"])

        await KeycloakAdminService.delete_tenant_group(tenant_id)

        with pytest.raises(KeycloakGetError):
            await admin.a_get_group_by_path(f"/tenants/{tenant_id}")


class TestActiveTenantAttribute:
    @pytest.mark.asyncio
    async def test_set_active_tenant(self, admin: KeycloakAdmin, seeded_user: tuple[str, str]) -> None:
        user_id, _ = seeded_user
        tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"

        await KeycloakAdminService.set_active_tenant(user_id, tenant_id)

        raw = await admin.a_get_user(user_id)
        assert raw.get("attributes", {}).get("active_tenant_id") == [tenant_id]

    @pytest.mark.asyncio
    async def test_get_active_tenant_id(self, admin: KeycloakAdmin, seeded_user: tuple[str, str]) -> None:
        user_id, _ = seeded_user
        tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"
        raw = await admin.a_get_user(user_id)
        raw["attributes"] = {"active_tenant_id": [tenant_id]}
        await admin.a_update_user(user_id, raw)

        result = await KeycloakAdminService.get_active_tenant_id(user_id)

        assert result == tenant_id

    @pytest.mark.asyncio
    async def test_get_active_tenant_id_returns_none_when_unset(self, seeded_user: tuple[str, str]) -> None:
        user_id, _ = seeded_user
        assert await KeycloakAdminService.get_active_tenant_id(user_id) is None

    @pytest.mark.asyncio
    async def test_clear_active_tenant(self, admin: KeycloakAdmin, seeded_user: tuple[str, str]) -> None:
        user_id, _ = seeded_user
        raw = await admin.a_get_user(user_id)
        raw["attributes"] = {"active_tenant_id": [f"itest-tenant-{uuid.uuid4().hex[:8]}"]}
        await admin.a_update_user(user_id, raw)

        await KeycloakAdminService.clear_active_tenant(user_id)

        raw_after = await admin.a_get_user(user_id)
        assert "active_tenant_id" not in raw_after.get("attributes", {})

    @pytest.mark.asyncio
    async def test_set_preserves_other_user_data(self, admin: KeycloakAdmin, seeded_user: tuple[str, str]) -> None:
        """Guards the GET-merge-PUT logic: setting the attribute must not wipe `firstName`."""
        user_id, _ = seeded_user
        raw = await admin.a_get_user(user_id)
        raw["firstName"] = "Integration"
        raw["lastName"] = "Test"
        await admin.a_update_user(user_id, raw)

        tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"
        await KeycloakAdminService.set_active_tenant(user_id, tenant_id)

        raw_after = await admin.a_get_user(user_id)
        assert raw_after["firstName"] == "Integration"
        assert raw_after["lastName"] == "Test"
        assert raw_after["attributes"]["active_tenant_id"] == [tenant_id]

    @pytest.mark.asyncio
    async def test_get_user_ids_with_active_tenant(self, admin: KeycloakAdmin) -> None:
        """Critical path: exercises `q=active_tenant_id:<id>` server-side attribute search."""
        tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"
        created_ids: list[str] = []
        try:
            for _ in range(3):
                email = f"itest-{uuid.uuid4().hex[:8]}@example.com"
                uid = await admin.a_create_user({"email": email, "username": email, "enabled": True})
                created_ids.append(uid)
            matching = set(created_ids[:2])
            for uid in matching:
                raw = await admin.a_get_user(uid)
                raw["attributes"] = {"active_tenant_id": [tenant_id]}
                await admin.a_update_user(uid, raw)

            result = await KeycloakAdminService.get_user_ids_with_active_tenant(tenant_id)

            assert result == matching
        finally:
            for uid in created_ids:
                with contextlib.suppress(KeycloakDeleteError, KeycloakGetError):
                    await admin.a_delete_user(uid)

    @pytest.mark.asyncio
    async def test_get_user_ids_with_active_tenant_empty(self) -> None:
        fresh_tenant_id = f"itest-tenant-{uuid.uuid4().hex[:8]}"
        result = await KeycloakAdminService.get_user_ids_with_active_tenant(fresh_tenant_id)
        assert result == set()


class TestAccessChangeHookNotified:
    @pytest.mark.asyncio
    async def test_set_active_tenant_notifies_hook(
        self, seeded_user: tuple[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from swiss_ai_hub.core.persistence.access import access_change_hook as hook_module

        assert not inspect.iscoroutinefunction(hook_module.AccessChangeHook.notify), (
            "AccessChangeHook.notify became async — update these tests to use AsyncMock."
        )
        calls = {"count": 0}
        monkeypatch.setattr(
            hook_module.AccessChangeHook,
            "notify",
            classmethod(lambda cls: calls.__setitem__("count", calls["count"] + 1)),
        )

        user_id, _ = seeded_user
        await KeycloakAdminService.set_active_tenant(user_id, f"itest-tenant-{uuid.uuid4().hex[:8]}")

        assert calls["count"] == 1

    @pytest.mark.asyncio
    async def test_clear_active_tenant_notifies_hook(
        self, admin: KeycloakAdmin, seeded_user: tuple[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from swiss_ai_hub.core.persistence.access import access_change_hook as hook_module

        assert not inspect.iscoroutinefunction(hook_module.AccessChangeHook.notify), (
            "AccessChangeHook.notify became async — update these tests to use AsyncMock."
        )
        user_id, _ = seeded_user
        raw = await admin.a_get_user(user_id)
        raw["attributes"] = {"active_tenant_id": [f"itest-tenant-{uuid.uuid4().hex[:8]}"]}
        await admin.a_update_user(user_id, raw)

        calls = {"count": 0}
        monkeypatch.setattr(
            hook_module.AccessChangeHook,
            "notify",
            classmethod(lambda cls: calls.__setitem__("count", calls["count"] + 1)),
        )

        await KeycloakAdminService.clear_active_tenant(user_id)

        assert calls["count"] == 1
