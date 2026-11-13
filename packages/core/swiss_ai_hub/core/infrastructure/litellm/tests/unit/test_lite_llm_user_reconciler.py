import asyncio
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, call, patch

import pytest

from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_admin_service import LiteLLMUserAdminService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_reconciler import LiteLLMUserReconciler

pytestmark = pytest.mark.unit

FLAG = LiteLLMUserAdminService.KEYS_BLOCKED_BY_HUB
HUB_ROLE = LiteLLMUserAdminService.HUB_USER_ROLE


class _World:
    """Keycloak's users and LiteLLM's users and keys as one run sees them, with every write recorded."""

    def __init__(self) -> None:
        self.enabled_by_user_id: dict[str, bool] = {}
        self.keycloak_user_ids: set[str] | None = None
        self.users: list[dict[str, Any]] = []
        self.keys: list[dict[str, Any]] = []
        self.update_user = AsyncMock()
        self.post = AsyncMock()
        self.delete_user = AsyncMock()
        self.user_exists = AsyncMock(side_effect=self._user_exists)
        self.list_users = AsyncMock(side_effect=lambda: self.users)

    def keycloak_user(self, user_id: str, *, enabled: bool = True) -> None:
        self.enabled_by_user_id[user_id] = enabled

    def litellm_user(
        self, user_id: str, *, role: str = HUB_ROLE, metadata: dict | None = None, **limits: Any
    ) -> dict[str, Any]:
        row = {"user_id": user_id, "user_role": role, "metadata": metadata or {}, **limits}
        self.users.append(row)
        return row

    def key(self, user_id: str, token: str, *, blocked: bool | None = None) -> None:
        self.keys.append({"user_id": user_id, "token": token, "blocked": blocked})

    def writes(self) -> list[Any]:
        return [*self.update_user.call_args_list, *self.post.call_args_list, *self.delete_user.call_args_list]

    async def _user_exists(self, user_id: str) -> bool:
        known = self.keycloak_user_ids if self.keycloak_user_ids is not None else set(self.enabled_by_user_id)
        return user_id in known


@pytest.fixture
def world() -> Iterator[_World]:
    world = _World()
    with (
        patch.object(
            KeycloakAdminService, "get_enabled_by_user_id", AsyncMock(side_effect=lambda: world.enabled_by_user_id)
        ),
        patch.object(KeycloakAdminService, "user_exists", world.user_exists),
        patch.object(LiteLLMUserAdminService, "list_users", world.list_users),
        patch.object(LiteLLMUserAdminService, "list_keys", AsyncMock(side_effect=lambda: world.keys)),
        patch.object(LiteLLMUserAdminService, "delete_user", world.delete_user),
        patch.object(LiteLLMUserAdminService, "_update_user", world.update_user),
        patch.object(LiteLLMUserAdminService, "_post", world.post),
    ):
        yield world


def _reconciler(redis: AsyncMock | None = None, **settings: Any) -> LiteLLMUserReconciler:
    return LiteLLMUserReconciler(
        redis=redis or AsyncMock(), settings=LiteLLMProxySettings(BASE_URL="http://litellm:4000", **settings)
    )


@pytest.mark.asyncio
async def test_an_enabled_user_whose_limits_match_is_left_alone(world: _World) -> None:
    world.keycloak_user("u1")
    world.litellm_user("u1", rpm_limit=60, budget_duration="30d")
    world.key("u1", "hash-1")

    report = await _reconciler(USER_RPM_LIMIT=60, USER_BUDGET_DURATION="30d").reconcile()

    assert world.writes() == []
    assert report.limits_updated_user_ids == []


@pytest.mark.asyncio
async def test_an_enabled_user_gets_the_changed_limits_only(world: _World) -> None:
    world.keycloak_user("u1")
    world.litellm_user("u1", rpm_limit=30, budget_duration="30d")

    report = await _reconciler(USER_RPM_LIMIT=60, USER_BUDGET_DURATION="30d").reconcile()

    assert world.update_user.call_args_list == [call("u1", {"rpm_limit": 60})]
    assert report.limits_updated_user_ids == ["u1"]


@pytest.mark.asyncio
async def test_a_disabled_users_keys_are_blocked_and_their_limits_left_alone(world: _World) -> None:
    world.keycloak_user("u1", enabled=False)
    world.litellm_user("u1", rpm_limit=30)
    world.key("u1", "hash-1")

    report = await _reconciler(USER_RPM_LIMIT=60).reconcile()

    assert world.update_user.call_args_list == [call("u1", {"metadata": {FLAG: ["hash-1"]}})]
    assert world.post.call_args_list == [call("/key/block", {"key": "hash-1"})]
    assert report.blocked_user_ids == ["u1"]


@pytest.mark.asyncio
async def test_a_disabled_user_already_blocked_is_left_alone(world: _World) -> None:
    world.keycloak_user("u1", enabled=False)
    world.litellm_user("u1", metadata={FLAG: ["hash-1"]})
    world.key("u1", "hash-1", blocked=True)

    report = await _reconciler().reconcile()

    assert world.writes() == []
    assert report.blocked_user_ids == []


@pytest.mark.asyncio
async def test_a_key_minted_after_the_block_is_blocked_too(world: _World) -> None:
    world.keycloak_user("u1", enabled=False)
    world.litellm_user("u1", metadata={FLAG: ["hash-old"]})
    world.key("u1", "hash-old", blocked=True)
    world.key("u1", "hash-new")

    await _reconciler().reconcile()

    assert world.update_user.call_args_list == [call("u1", {"metadata": {FLAG: ["hash-old", "hash-new"]}})]
    assert world.post.call_args_list == [call("/key/block", {"key": "hash-new"})]


@pytest.mark.asyncio
async def test_a_user_enabled_again_has_the_keys_the_hub_blocked_unblocked(world: _World) -> None:
    world.keycloak_user("u1")
    world.litellm_user("u1", metadata={FLAG: ["hash-1"]})
    world.key("u1", "hash-1", blocked=True)

    report = await _reconciler().reconcile()

    assert world.post.call_args_list == [call("/key/unblock", {"key": "hash-1"})]
    assert world.update_user.call_args_list == [call("u1", {"metadata": {FLAG: []}})]
    assert report.unblocked_user_ids == ["u1"]


@pytest.mark.asyncio
async def test_a_key_blocked_by_hand_stays_blocked(world: _World) -> None:
    world.keycloak_user("u1")
    world.litellm_user("u1")
    world.key("u1", "hash-1", blocked=True)

    await _reconciler().reconcile()

    assert world.writes() == []


@pytest.mark.asyncio
async def test_a_key_blocked_by_hand_before_the_user_was_disabled_stays_blocked_after_re_enabling(
    world: _World,
) -> None:
    world.keycloak_user("u1", enabled=False)
    user_row = world.litellm_user("u1")
    world.key("u1", "hash-blocked-by-hand", blocked=True)
    world.key("u1", "hash-usable")

    await _reconciler().reconcile()
    user_row["metadata"] = world.update_user.call_args.args[1]["metadata"]
    world.keys[1]["blocked"] = True
    world.keycloak_user("u1")
    await _reconciler().reconcile()

    assert [request.args for request in world.post.call_args_list] == [
        ("/key/block", {"key": "hash-usable"}),
        ("/key/unblock", {"key": "hash-usable"}),
    ]


@pytest.mark.asyncio
async def test_a_hub_user_keycloak_no_longer_has_is_deleted_and_reported(world: _World) -> None:
    world.keycloak_user("someone-else")
    world.litellm_user("gone")
    world.key("gone", "hash-1")

    report = await _reconciler().reconcile()

    assert world.delete_user.call_args_list == [call("gone")]
    assert report.users_without_hub_user == ["gone"]
    assert report.deleted_user_ids == ["gone"]


@pytest.mark.asyncio
async def test_a_user_who_signed_up_after_the_listing_is_left_alone(world: _World) -> None:
    world.keycloak_user("someone-else")
    world.keycloak_user_ids = {"someone-else", "new"}
    world.litellm_user("new")

    report = await _reconciler().reconcile()

    assert world.writes() == []
    assert report.users_without_hub_user == []


@pytest.mark.asyncio
async def test_a_user_the_hub_did_not_create_is_only_reported(world: _World) -> None:
    world.keycloak_user("someone-else")
    world.litellm_user("made-by-hand", role="internal_user")

    report = await _reconciler().reconcile()

    assert world.writes() == []
    assert report.users_without_hub_user == ["made-by-hand"]
    assert report.deleted_user_ids == []


@pytest.mark.asyncio
async def test_keys_whose_user_has_no_litellm_user_are_reported_with_their_keycloak_state(world: _World) -> None:
    world.keycloak_user("enabled-without-row")
    world.keycloak_user("disabled-without-row", enabled=False)
    world.keycloak_user("with-row")
    world.litellm_user("with-row")
    world.litellm_user("test-identity")
    for user_id in ("enabled-without-row", "disabled-without-row", "gone-without-row", "with-row", "test-identity"):
        world.key(user_id, f"hash-{user_id}")
    world.keys.append({"user_id": None, "token": "hash-service", "blocked": None})

    report = await _reconciler(USER_RECONCILE_EXEMPT_USER_IDS="test-identity").reconcile()

    assert world.writes() == []
    assert report.keycloak_state_by_user_id_without_row == {
        "disabled-without-row": "disabled",
        "enabled-without-row": "enabled",
        "gone-without-row": "not in Keycloak",
    }


@pytest.mark.asyncio
async def test_litellms_admin_and_exempt_users_are_neither_reported_nor_touched(world: _World) -> None:
    world.keycloak_user("someone-else")
    world.litellm_user(LiteLLMUserReconciler.LITELLM_ADMIN_USER_ID, role="proxy_admin")
    world.litellm_user("test-identity")

    report = await _reconciler(USER_RECONCILE_EXEMPT_USER_IDS="test-identity").reconcile()

    assert world.writes() == []
    assert world.user_exists.await_count == 0
    assert report.users_without_hub_user == []


@pytest.mark.asyncio
async def test_an_outage_while_confirming_a_removal_deletes_nothing(world: _World) -> None:
    world.keycloak_user("someone-else")
    world.litellm_user("unknown")
    world.user_exists.side_effect = ConnectionError("Keycloak unreachable")

    reconciler = _reconciler()
    with pytest.raises(ExceptionGroup) as raised:
        await reconciler.reconcile()

    assert raised.group_contains(ConnectionError)

    assert world.delete_user.await_count == 0


@pytest.mark.asyncio
async def test_an_empty_realm_stops_the_run_before_litellm_is_read(world: _World) -> None:
    world.litellm_user("u1")

    reconciler = _reconciler()
    with pytest.raises(RuntimeError, match="no users"):
        await reconciler.reconcile()

    assert world.list_users.await_count == 0


@pytest.mark.asyncio
async def test_access_is_withdrawn_before_a_failing_limit_update(world: _World) -> None:
    """A user listed first whose update LiteLLM rejects must not keep a disabled user's key working."""
    world.keycloak_user("drifted")
    world.keycloak_user("disabled", enabled=False)
    world.litellm_user("drifted", rpm_limit=30)
    world.litellm_user("disabled")
    world.key("disabled", "hash-disabled")

    async def reject_limits(user_id: str, fields: dict) -> None:
        if "rpm_limit" in fields:
            raise RuntimeError("LiteLLM rejected the update")

    world.update_user.side_effect = reject_limits

    reconciler = _reconciler(USER_RPM_LIMIT=60)
    with pytest.raises(ExceptionGroup) as raised:
        await reconciler.reconcile()

    assert raised.group_contains(RuntimeError, match="rejected")
    assert world.post.call_args_list == [call("/key/block", {"key": "hash-disabled"})]


@pytest.mark.asyncio
async def test_a_failing_limit_update_does_not_keep_a_re_enabled_user_locked_out(world: _World) -> None:
    world.keycloak_user("drifted")
    world.keycloak_user("re-enabled")
    world.litellm_user("drifted", rpm_limit=30)
    world.litellm_user("re-enabled", rpm_limit=60, metadata={FLAG: ["hash-1"]})
    world.key("re-enabled", "hash-1", blocked=True)

    async def reject_limits(user_id: str, fields: dict) -> None:
        if "rpm_limit" in fields:
            raise RuntimeError("LiteLLM rejected the update")

    world.update_user.side_effect = reject_limits

    reconciler = _reconciler(USER_RPM_LIMIT=60)
    with pytest.raises(ExceptionGroup):
        await reconciler.reconcile()

    assert world.post.call_args_list == [call("/key/unblock", {"key": "hash-1"})]


@pytest.mark.asyncio
async def test_one_users_failing_block_does_not_keep_another_disabled_users_key_working(world: _World) -> None:
    for user_id in ("first", "second"):
        world.keycloak_user(user_id, enabled=False)
        world.litellm_user(user_id)
        world.key(user_id, f"hash-{user_id}")

    async def reject_first(path: str, body: dict) -> None:
        if body == {"key": "hash-first"}:
            raise RuntimeError("LiteLLM rejected the block")

    world.post.side_effect = reject_first

    reconciler = _reconciler()
    with pytest.raises(ExceptionGroup) as raised:
        await reconciler.reconcile()

    assert raised.group_contains(RuntimeError, match="rejected the block")
    assert call("/key/block", {"key": "hash-second"}) in world.post.call_args_list


@pytest.mark.asyncio
async def test_a_run_is_skipped_while_another_replica_holds_the_lease(world: _World) -> None:
    world.keycloak_user("u1")
    redis = AsyncMock()
    redis.set.return_value = False

    await _reconciler(redis).run_if_due()

    assert world.list_users.await_count == 0


@pytest.mark.asyncio
async def test_a_run_holds_the_lease_for_one_interval(world: _World) -> None:
    world.keycloak_user("u1")
    redis = AsyncMock()
    redis.set.return_value = True

    await _reconciler(redis, USER_RECONCILE_INTERVAL_SECONDS=120).run_if_due()

    assert redis.set.call_args == call("litellm:user-reconciliation:lease", "held", nx=True, px=120_000)
    assert world.list_users.await_count == 1


@pytest.mark.asyncio
async def test_a_run_is_cut_off_when_its_lease_expires(world: _World) -> None:
    """Two overlapping runs could clear the record of keys the other is about to block."""
    world.keycloak_user("u1")

    async def outlive_the_lease() -> list:
        await asyncio.sleep(1)
        return []

    world.list_users.side_effect = outlive_the_lease
    redis = AsyncMock()
    redis.set.return_value = True

    reconciler = _reconciler(redis, USER_RECONCILE_INTERVAL_SECONDS=0.05)
    with pytest.raises(TimeoutError):
        await reconciler.run_if_due()
