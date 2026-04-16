from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from swiss_ai_hub.core.auth.usage.rate_limit_store import CounterState, RateLimitStore
from swiss_ai_hub.core.auth.usage.usage_limit_models import ResourceType, RoleUsageLimit, UsageLimitPeriod
from swiss_ai_hub.core.auth.usage.usage_limits import UsageLimits
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401


AGENT_PREFIX = "aihub.user.agent."
TEST_TENANT_ID = "test-tenant"


def rl(pattern: str, limit: int, period: str) -> RoleUsageLimit:
    """Shorthand factory for test readability."""
    return RoleUsageLimit(pattern=pattern, limit=limit, period=period)


def create_service(mock_redis: AsyncMock | None = None) -> UsageLimits:
    """Create a UsageLimits with a mocked Redis."""
    if mock_redis is None:
        mock_redis = AsyncMock()
    return UsageLimits(mock_redis)


def create_service_with_store(store: RateLimitStore) -> UsageLimits:
    """Create a UsageLimits and inject a pre-built store."""
    redis = AsyncMock()
    service = UsageLimits(redis)
    service._store_for_user = MagicMock(return_value=store)
    return service


class TestPatternMatching:
    """Tests for UsageLimits._pattern_matches"""

    def test_wildcard_gt_matches_any_path(self):
        assert UsageLimits._pattern_matches(f"{AGENT_PREFIX}>", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent")

    def test_wildcard_gt_matches_single_segment(self):
        assert UsageLimits._pattern_matches(f"{AGENT_PREFIX}>", f"{AGENT_PREFIX}LLMWrappingAgent")

    def test_agent_class_gt_matches_any_agent_id(self):
        assert UsageLimits._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.>", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

    def test_agent_class_gt_does_not_match_different_class(self):
        assert not UsageLimits._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.>", f"{AGENT_PREFIX}RagAgent.dev_agent"
        )

    def test_exact_match(self):
        assert UsageLimits._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

    def test_exact_no_match(self):
        assert not UsageLimits._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent", f"{AGENT_PREFIX}LLMWrappingAgent.other"
        )

    def test_star_matches_single_level(self):
        assert UsageLimits._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.*", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

    def test_star_does_not_match_multi_level(self):
        assert not UsageLimits._pattern_matches(f"{AGENT_PREFIX}*", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent")

    def test_gt_requires_at_least_one_segment(self):
        assert UsageLimits._pattern_matches(f"{AGENT_PREFIX}>", f"{AGENT_PREFIX}anything")


class TestSpecificity:
    """Tests for UsageLimits._specificity"""

    def test_gt_only(self):
        assert UsageLimits._specificity(f"{AGENT_PREFIX}>") == 3  # aihub, user, agent

    def test_class_gt(self):
        assert UsageLimits._specificity(f"{AGENT_PREFIX}LLMWrappingAgent.>") == 4

    def test_exact(self):
        assert UsageLimits._specificity(f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent") == 5

    def test_star_not_counted(self):
        assert UsageLimits._specificity(f"{AGENT_PREFIX}LLMWrappingAgent.*") == 4


class TestGetEffectiveLimitsForRoles:
    """Tests for UsageLimits.get_effective_limits_for_roles"""

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_unlimited_when_no_roles_have_limits(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[], []]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1", "role2"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert limits == []

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_returns_empty_when_no_roles(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = []

        limits = UsageLimits.get_effective_limits_for_roles([], TEST_TENANT_ID)

        assert limits == []

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_single_role_with_catchall(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 100
        assert limits[0].period == "1d"
        assert limits[0].pattern == f"{AGENT_PREFIX}>"

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_all_matching_patterns_returned_independently(self, mock_role_entity: MagicMock):
        """Both catchall and class-level patterns should be returned as independent limits."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h"),
            ],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 2
        patterns = {el.pattern for el in limits}
        assert f"{AGENT_PREFIX}>" in patterns
        assert f"{AGENT_PREFIX}LLMWrappingAgent.>" in patterns

        catchall = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}>")
        assert catchall.limit == 100
        assert catchall.period == "1d"

        class_level = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>")
        assert class_level.limit == 20
        assert class_level.period == "1h"

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_same_pattern_across_roles_highest_limit_wins(self, mock_role_entity: MagicMock):
        """For the same pattern across roles, take the highest limit."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [rl(f"{AGENT_PREFIX}>", 200, "1d")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1", "role2"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 200
        assert limits[0].period == "1d"

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_different_patterns_across_roles_are_independent(self, mock_role_entity: MagicMock):
        """
        Role A: > = 50/day
        Role B: > = 100/day, LLMWrappingAgent.> = 10/hour
        Result: > = 100/day (highest), LLMWrappingAgent.> = 10/hour (only from B)
        """
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["roleA", "roleB"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 2
        catchall = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}>")
        assert catchall.limit == 100

        class_level = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>")
        assert class_level.limit == 10
        assert class_level.period == "1h"

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_no_matching_pattern_returns_empty(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}RagAgent.>", 10, "1h")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert limits == []

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_no_resource_path_picks_most_permissive_rule(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(["role1"], TEST_TENANT_ID)

        assert len(limits) == 1
        assert limits[0].limit == 100
        assert limits[0].period == "1d"

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_role_without_limits_grants_unlimited(self, mock_role_entity: MagicMock):
        """A role without limits means unlimited — if any role is unlimited, user is unlimited."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1", "role2"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert limits == []

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_three_levels_all_returned(self, mock_role_entity: MagicMock):
        """Catchall + class-level + instance-level: all three are independent limits."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 50, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent", 10, "1h"),
            ],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 3
        patterns = {el.pattern for el in limits}
        assert f"{AGENT_PREFIX}>" in patterns
        assert f"{AGENT_PREFIX}LLMWrappingAgent.>" in patterns
        assert f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent" in patterns


class TestGetEffectiveLimitForRoles:
    """Tests for get_effective_limit_for_roles (single most specific)."""

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_returns_most_specific(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h"),
            ],
        ]

        result = UsageLimits.get_effective_limit_for_roles(
            ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert result is not None
        assert result.limit == 20
        assert result.period == "1h"
        assert result.pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>"

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_returns_none_when_no_limits(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]

        result = UsageLimits.get_effective_limit_for_roles(
            ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}Foo.bar"
        )

        assert result is None


class TestGetUsageStatus:
    """Tests for UsageLimits.get_usage_status"""

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_unlimited_user_returns_empty_limits(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]
        store = AsyncMock(spec=RateLimitStore)
        service = create_service_with_store(store)

        status = await service.get_usage_status("user123", ["admin"], TEST_TENANT_ID)

        assert status.limits == []
        assert status.is_exceeded is False
        store.get_counts.assert_not_called()

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_returns_all_matching_limits_with_counts(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        store = AsyncMock(spec=RateLimitStore)
        store.get_counts.return_value = [CounterState(42, None), CounterState(5, None)]
        service = create_service_with_store(store)

        status = await service.get_usage_status(
            "user123", ["user"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert len(status.limits) == 2
        assert status.is_exceeded is False

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_exceeded_when_any_limit_at_capacity(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        store = AsyncMock(spec=RateLimitStore)
        # catchall: 42/100 (ok), class: 10/10 (exceeded)
        store.get_counts.return_value = [CounterState(42, None), CounterState(10, None)]
        service = create_service_with_store(store)

        status = await service.get_usage_status(
            "user123", ["user"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert status.is_exceeded is True
        exceeded_limits = [ls for ls in status.limits if ls.is_exceeded]
        assert len(exceeded_limits) == 1
        assert exceeded_limits[0].pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>"


class TestCheckAndIncrement:
    """Tests for UsageLimits.check_and_increment (atomic Lua script)."""

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_unlimited_does_not_increment(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]
        store = AsyncMock(spec=RateLimitStore)
        service = create_service_with_store(store)

        status = await service.check_and_increment("user123", ["admin"], TEST_TENANT_ID)

        assert status.limits == []
        assert status.is_exceeded is False
        store.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_increments_all_matching_counters(self, mock_role_entity: MagicMock):
        """With catchall + class-level, a single atomic call increments both counters."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h")]
        ]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (True, [CounterState(6, None), CounterState(4, None)])
        service = create_service_with_store(store)

        status = await service.check_and_increment(
            "user1", ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert len(status.limits) == 2
        assert status.is_exceeded is False
        store.check_and_increment.assert_called_once()

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_does_not_increment_any_when_one_exceeded(self, mock_role_entity: MagicMock):
        """If any limit is exceeded, the store returns pre-increment counts."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (False, [CounterState(5, None), CounterState(10, None)])
        service = create_service_with_store(store)

        status = await service.check_and_increment(
            "user1", ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert status.is_exceeded is True
        store.check_and_increment.assert_called_once()

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_single_limit_increments_atomically(self, mock_role_entity: MagicMock):
        """Single limit uses the same atomic call."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [[rl(f"{AGENT_PREFIX}>", 100, "1d")]]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (True, [CounterState(1, None)])
        service = create_service_with_store(store)

        await service.check_and_increment(
            "user123", ["user"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        store.check_and_increment.assert_called_once()


class TestMultiRoleWithIndependentLimits:
    """Multi-role scenarios with independent limits."""

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_same_pattern_across_roles_highest_wins(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [rl(f"{AGENT_PREFIX}>", 200, "1d")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["roleA", "roleB"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 200

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_different_patterns_stay_independent(self, mock_role_entity: MagicMock):
        """
        Role A: > = 50/day, LLMWrappingAgent.> = 10/hour
        Role B: > = 100/day
        Result: > = 100/day, LLMWrappingAgent.> = 10/hour
        """
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")],
            [rl(f"{AGENT_PREFIX}>", 100, "1d")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["roleA", "roleB"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 2
        catchall = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}>")
        assert catchall.limit == 100

        class_level = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>")
        assert class_level.limit == 10

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_three_roles_highest_per_pattern(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 10, "1d")],
            [rl(f"{AGENT_PREFIX}>", 500, "1d")],
            [rl(f"{AGENT_PREFIX}>", 100, "1d")],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["r1", "r2", "r3"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 500

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_both_roles_no_limits_means_unlimited(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[], []]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["roleA", "roleB"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert limits == []


class TestCheckAndIncrementIntegration:
    """End-to-end check_and_increment with multi-limit enforcement."""

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_increments_all_counters_when_none_exceeded(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h")],
        ]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (True, [CounterState(4, None), CounterState(6, None)])
        service = create_service_with_store(store)

        status = await service.check_and_increment(
            "user1", ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert status.is_exceeded is False
        store.check_and_increment.assert_called_once()

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_blocks_when_class_level_exceeded_catchall_ok(self, mock_role_entity: MagicMock):
        """Even though catchall has room, class-level exceeded blocks the call."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")],
        ]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (False, [CounterState(5, None), CounterState(10, None)])
        service = create_service_with_store(store)

        status = await service.check_and_increment(
            "user1", ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert status.is_exceeded is True
        store.check_and_increment.assert_called_once()

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_multi_role_highest_limit_applied_per_pattern(self, mock_role_entity: MagicMock):
        """Two roles with same catchall → highest wins, both limits enforced."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [rl(f"{AGENT_PREFIX}>", 200, "1d")],
        ]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (True, [CounterState(61, None)])
        service = create_service_with_store(store)

        status = await service.check_and_increment(
            "user1", ["roleA", "roleB"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert status.is_exceeded is False
        assert len(status.limits) == 1
        assert status.limits[0].limit == 200
        assert status.limits[0].current_count == 61


class TestBackwardCompatProperties:
    """Test backward-compat properties on UsageStatus."""

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_limit_property_returns_most_restrictive(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        store = AsyncMock(spec=RateLimitStore)
        store.get_counts.return_value = [CounterState(42, None), CounterState(9, None)]
        service = create_service_with_store(store)

        status = await service.get_usage_status(
            "user1", ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        # 9/10 = 0.9 ratio vs 42/100 = 0.42 ratio → class-level is most restrictive
        assert status.limit == 10
        assert status.period == "1h"
        assert status.current_count == 9

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_properties_return_none_when_unlimited(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]
        store = AsyncMock(spec=RateLimitStore)
        service = create_service_with_store(store)

        status = await service.get_usage_status("user1", ["admin"], TEST_TENANT_ID)

        assert status.limit is None
        assert status.period is None
        assert status.current_count == 0
        assert status.reset_at is None


class TestPeriodConstants:
    """Tests for period duration constants."""

    def test_all_periods_have_durations(self):
        for period in UsageLimitPeriod:
            assert period.seconds > 0

    def test_period_durations_are_correct(self):
        assert UsageLimitPeriod.ONE_HOUR.seconds == 3600
        assert UsageLimitPeriod.ONE_DAY.seconds == 86400
        assert UsageLimitPeriod.SEVEN_DAYS.seconds == 604800
        assert UsageLimitPeriod.ONE_MONTH.seconds == 2592000


class TestPatternPeriodCombinations:
    """Tests for (pattern, period) handling - duplicates prevented at RoleEntity level."""

    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    def test_same_pattern_different_periods_kept_independently(self, mock_role_entity: MagicMock):
        """Same pattern with different periods are independent limits, both kept."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}>", 20, "1h"),
            ],
        ]

        limits = UsageLimits.get_effective_limits_for_roles(
            ["role1"], TEST_TENANT_ID, resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 2
        periods = {limit.period for limit in limits}
        assert "1d" in periods
        assert "1h" in periods


class TestCheckAndRaise:
    """Tests for UsageLimits.check_and_raise (HTTP 429 path)."""

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_raises_429_when_exceeded(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[rl(f"{AGENT_PREFIX}>", 10, "1h")]]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (False, [CounterState(10, None)])
        service = create_service_with_store(store)

        user = MagicMock()
        user.id = "user123"
        user.roles = ["role1"]
        user.acting_within_tenant.id = TEST_TENANT_ID

        with pytest.raises(HTTPException) as exc_info:
            await service.check_and_raise(user, ResourceType.AGENT, "MyAgent", "v1", locale="en")

        assert exc_info.value.status_code == 429
        detail = exc_info.value.detail
        assert detail["error"] == "usage_limit_exceeded"
        assert detail["limit"] == 10
        assert detail["period"] == "1h"

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_does_not_raise_when_within_limit(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[rl(f"{AGENT_PREFIX}>", 100, "1d")]]
        store = AsyncMock(spec=RateLimitStore)
        store.check_and_increment.return_value = (True, [CounterState(5, None)])
        service = create_service_with_store(store)

        user = MagicMock()
        user.id = "user123"
        user.roles = ["role1"]
        user.acting_within_tenant.id = TEST_TENANT_ID

        status = await service.check_and_raise(user, ResourceType.AGENT, "MyAgent", "v1", locale="en")

        assert status.is_exceeded is False

    @pytest.mark.asyncio
    @patch("swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity")
    async def test_unlimited_user_passes(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]
        store = AsyncMock(spec=RateLimitStore)
        service = create_service_with_store(store)

        user = MagicMock()
        user.id = "user123"
        user.roles = ["admin"]
        user.acting_within_tenant.id = TEST_TENANT_ID

        status = await service.check_and_raise(user, ResourceType.AGENT, "MyAgent", "v1", locale="en")

        assert status.is_exceeded is False
        assert status.limits == []
