from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aihub_lib.auth.usage.UsageLimitService import (
    UsageLimitPeriod,
    UsageLimitService,
)
from aihub_lib.persistence.access.entities.RoleEntity import RoleUsageLimit

AGENT_PREFIX = "aihub.user.agent."


def rl(pattern: str, limit: int, period: str) -> RoleUsageLimit:
    """Shorthand factory for test readability."""
    return RoleUsageLimit(pattern=pattern, limit=limit, period=period)


class TestPatternMatching:
    """Tests for UsageLimitService._pattern_matches"""

    def test_wildcard_gt_matches_any_path(self):
        assert UsageLimitService._pattern_matches(f"{AGENT_PREFIX}>", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent")

    def test_wildcard_gt_matches_single_segment(self):
        assert UsageLimitService._pattern_matches(f"{AGENT_PREFIX}>", f"{AGENT_PREFIX}LLMWrappingAgent")

    def test_agent_class_gt_matches_any_agent_id(self):
        assert UsageLimitService._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.>", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

    def test_agent_class_gt_does_not_match_different_class(self):
        assert not UsageLimitService._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.>", f"{AGENT_PREFIX}RagAgent.dev_agent"
        )

    def test_exact_match(self):
        assert UsageLimitService._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

    def test_exact_no_match(self):
        assert not UsageLimitService._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent", f"{AGENT_PREFIX}LLMWrappingAgent.other"
        )

    def test_star_matches_single_level(self):
        assert UsageLimitService._pattern_matches(
            f"{AGENT_PREFIX}LLMWrappingAgent.*", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

    def test_star_does_not_match_multi_level(self):
        assert not UsageLimitService._pattern_matches(f"{AGENT_PREFIX}*", f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent")

    def test_gt_requires_at_least_one_segment(self):
        assert UsageLimitService._pattern_matches(f"{AGENT_PREFIX}>", f"{AGENT_PREFIX}anything")


class TestSpecificity:
    """Tests for UsageLimitService._specificity"""

    def test_gt_only(self):
        assert UsageLimitService._specificity(f"{AGENT_PREFIX}>") == 3  # aihub, user, agent

    def test_class_gt(self):
        assert UsageLimitService._specificity(f"{AGENT_PREFIX}LLMWrappingAgent.>") == 4

    def test_exact(self):
        assert UsageLimitService._specificity(f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent") == 5

    def test_star_not_counted(self):
        assert UsageLimitService._specificity(f"{AGENT_PREFIX}LLMWrappingAgent.*") == 4


class TestGetEffectiveLimitsForRoles:
    """Tests for UsageLimitService.get_effective_limits_for_roles"""

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_unlimited_when_no_roles_have_limits(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[], []]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1", "role2"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert limits == []

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_returns_empty_when_no_roles(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = []

        limits = UsageLimitService.get_effective_limits_for_roles([])

        assert limits == []

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_single_role_with_catchall(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d")],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 100
        assert limits[0].period == "1d"
        assert limits[0].pattern == f"{AGENT_PREFIX}>"

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_all_matching_patterns_returned_independently(self, mock_role_entity: MagicMock):
        """Both catchall and class-level patterns should be returned as independent limits."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h"),
            ],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
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

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_same_pattern_across_roles_highest_limit_wins(self, mock_role_entity: MagicMock):
        """For the same pattern across roles, take the highest limit."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [rl(f"{AGENT_PREFIX}>", 200, "1d")],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1", "role2"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 200
        assert limits[0].period == "1d"

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
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

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["roleA", "roleB"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 2
        catchall = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}>")
        assert catchall.limit == 100

        class_level = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>")
        assert class_level.limit == 10
        assert class_level.period == "1h"

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_no_matching_pattern_returns_empty(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}RagAgent.>", 10, "1h")],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert limits == []

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_no_resource_path_picks_most_permissive_rule(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h")],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(["role1"])

        assert len(limits) == 1
        assert limits[0].limit == 100
        assert limits[0].period == "1d"

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_role_without_limits_contributes_nothing(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1", "role2"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 50

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_three_levels_all_returned(self, mock_role_entity: MagicMock):
        """Catchall + class-level + instance-level: all three are independent limits."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 50, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent", 10, "1h"),
            ],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 3
        patterns = {el.pattern for el in limits}
        assert f"{AGENT_PREFIX}>" in patterns
        assert f"{AGENT_PREFIX}LLMWrappingAgent.>" in patterns
        assert f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent" in patterns


class TestGetEffectiveLimitForRolesLegacy:
    """Tests for the legacy get_effective_limit_for_roles (single most specific)."""

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_returns_most_specific(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h"),
            ],
        ]

        limit, period, pattern = UsageLimitService.get_effective_limit_for_roles(
            ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert limit == 20
        assert period == "1h"
        assert pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>"


class TestGetUsageStatus:
    """Tests for UsageLimitService.get_usage_status"""

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_unlimited_user_returns_empty_limits(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]
        redis = AsyncMock()

        status = await UsageLimitService.get_usage_status(redis, "user123", ["admin"])

        assert status.limits == []
        assert status.is_exceeded is False
        redis.get.assert_not_called()

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_returns_all_matching_limits_with_counts(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        redis = AsyncMock()
        redis.get.side_effect = [b"42", b"5"]
        redis.ttl.side_effect = [3600, 1800]

        status = await UsageLimitService.get_usage_status(
            redis, "user123", ["user"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert len(status.limits) == 2
        assert status.is_exceeded is False

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_exceeded_when_any_limit_at_capacity(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        redis = AsyncMock()
        # catchall: 42/100 (ok), class: 10/10 (exceeded)
        redis.get.side_effect = [b"42", b"10"]
        redis.ttl.side_effect = [3600, 1800]

        status = await UsageLimitService.get_usage_status(
            redis, "user123", ["user"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert status.is_exceeded is True
        exceeded_limits = [ls for ls in status.limits if ls.is_exceeded]
        assert len(exceeded_limits) == 1
        assert exceeded_limits[0].pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>"


class TestCheckAndIncrement:
    """Tests for UsageLimitService.check_and_increment"""

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_unlimited_does_not_increment(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]
        redis = AsyncMock()

        status = await UsageLimitService.check_and_increment(redis, "user123", ["admin"])

        assert status.limits == []
        assert status.is_exceeded is False
        redis.incr.assert_not_called()

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_increments_all_matching_counters(self, mock_role_entity: MagicMock):
        """With catchall + class-level, BOTH Redis counters get incremented."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h")]
        ]
        redis = AsyncMock()
        redis.get.side_effect = [b"5", b"3"]
        redis.incr.side_effect = [6, 4]
        redis.ttl.return_value = 80000

        status = await UsageLimitService.check_and_increment(
            redis, "user1", ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert len(status.limits) == 2
        assert status.is_exceeded is False
        assert redis.incr.call_count == 2
        incr_keys = {call.args[0] for call in redis.incr.call_args_list}
        assert f"usage:calls:user1:{AGENT_PREFIX}>:1d" in incr_keys
        assert f"usage:calls:user1:{AGENT_PREFIX}LLMWrappingAgent.>:1h" in incr_keys

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_does_not_increment_any_when_one_exceeded(self, mock_role_entity: MagicMock):
        """If any limit is exceeded, NO counters get incremented."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        redis = AsyncMock()
        # catchall: 5/100 (ok), class: 10/10 (exceeded)
        redis.get.side_effect = [b"5", b"10"]
        redis.ttl.return_value = 1800

        status = await UsageLimitService.check_and_increment(
            redis, "user1", ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert status.is_exceeded is True
        redis.incr.assert_not_called()

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_sets_ttl_on_first_increment(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[rl(f"{AGENT_PREFIX}>", 100, "1d")]]
        redis = AsyncMock()
        redis.get.return_value = None
        redis.incr.return_value = 1
        redis.ttl.return_value = UsageLimitPeriod.ONE_DAY.seconds

        await UsageLimitService.check_and_increment(
            redis, "user123", ["user"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        redis.expire.assert_called_once_with(
            f"usage:calls:user123:{AGENT_PREFIX}>:1d", UsageLimitPeriod.ONE_DAY.seconds
        )

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_sets_ttl_on_all_counters_on_first_increment(self, mock_role_entity: MagicMock):
        """Both counters get TTL set when both are new (count=1)."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h")]
        ]
        redis = AsyncMock()
        redis.get.side_effect = [None, None]
        redis.incr.side_effect = [1, 1]
        redis.ttl.return_value = 3600

        await UsageLimitService.check_and_increment(
            redis, "user1", ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        assert redis.expire.call_count == 2


class TestMultiRoleWithIndependentLimits:
    """Multi-role scenarios with independent limits."""

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_same_pattern_across_roles_highest_wins(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [rl(f"{AGENT_PREFIX}>", 200, "1d")],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["roleA", "roleB"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 200

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
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

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["roleA", "roleB"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 2
        catchall = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}>")
        assert catchall.limit == 100

        class_level = next(el for el in limits if el.pattern == f"{AGENT_PREFIX}LLMWrappingAgent.>")
        assert class_level.limit == 10

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_three_roles_highest_per_pattern(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 10, "1d")],
            [rl(f"{AGENT_PREFIX}>", 500, "1d")],
            [rl(f"{AGENT_PREFIX}>", 100, "1d")],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["r1", "r2", "r3"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 500

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_both_roles_no_limits_means_unlimited(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[], []]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["roleA", "roleB"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert limits == []


class TestCheckAndIncrementIntegration:
    """End-to-end check_and_increment with multi-limit enforcement."""

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_increments_all_counters_when_none_exceeded(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 20, "1h")],
        ]
        redis = AsyncMock()
        redis.get.side_effect = [b"3", b"5"]
        redis.incr.side_effect = [4, 6]
        redis.ttl.return_value = 80000

        status = await UsageLimitService.check_and_increment(
            redis, "user1", ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert status.is_exceeded is False
        assert redis.incr.call_count == 2

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_blocks_when_class_level_exceeded_catchall_ok(self, mock_role_entity: MagicMock):
        """Even though catchall has room, class-level exceeded blocks the call."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")],
        ]
        redis = AsyncMock()
        redis.get.side_effect = [b"5", b"10"]  # catchall ok, class exceeded
        redis.ttl.return_value = 1800

        status = await UsageLimitService.check_and_increment(
            redis, "user1", ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert status.is_exceeded is True
        redis.incr.assert_not_called()

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_multi_role_highest_limit_applied_per_pattern(self, mock_role_entity: MagicMock):
        """Two roles with same catchall → highest wins, both limits enforced."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
            [rl(f"{AGENT_PREFIX}>", 200, "1d")],
        ]
        redis = AsyncMock()
        redis.get.return_value = b"60"  # 60 < 200, ok
        redis.incr.return_value = 61
        redis.ttl.return_value = 70000

        status = await UsageLimitService.check_and_increment(
            redis, "user1", ["roleA", "roleB"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert status.is_exceeded is False
        assert len(status.limits) == 1
        assert status.limits[0].limit == 200
        assert status.limits[0].current_count == 61


class TestBackwardCompatProperties:
    """Test backward-compat properties on UsageStatus."""

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_limit_property_returns_most_restrictive(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}LLMWrappingAgent.>", 10, "1h")]
        ]
        redis = AsyncMock()
        redis.get.side_effect = [b"42", b"9"]
        redis.ttl.return_value = 3600

        status = await UsageLimitService.get_usage_status(
            redis, "user1", ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev"
        )

        # 9/10 = 0.9 ratio vs 42/100 = 0.42 ratio → class-level is most restrictive
        assert status.limit == 10
        assert status.period == "1h"
        assert status.current_count == 9

    @pytest.mark.asyncio
    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    async def test_properties_return_none_when_unlimited(self, mock_role_entity: MagicMock):
        mock_role_entity.get_usage_limits_for_roles.return_value = [[]]
        redis = AsyncMock()

        status = await UsageLimitService.get_usage_status(redis, "user1", ["admin"])

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


class TestDuplicatePatternWithinSameRole:
    """Duplicate patterns within a single role should resolve to the most restrictive."""

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_same_pattern_within_role_picks_lowest_limit(self, mock_role_entity: MagicMock):
        """Two identical patterns on one role: the tighter limit (20) wins over the looser one (100)."""
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [
                rl(f"{AGENT_PREFIX}>", 100, "1d"),
                rl(f"{AGENT_PREFIX}>", 20, "1d"),
            ],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["role1"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 20

    @patch("aihub_lib.auth.usage.UsageLimitService.RoleEntity")
    def test_same_pattern_within_role_lowest_wins_then_cross_role_highest_wins(self, mock_role_entity: MagicMock):
        """
        Role A: > = 100/day and > = 20/day → intra-role dedup picks 20
        Role B: > = 50/day
        Cross-role merge: max(20, 50) = 50
        """
        mock_role_entity.get_usage_limits_for_roles.return_value = [
            [rl(f"{AGENT_PREFIX}>", 100, "1d"), rl(f"{AGENT_PREFIX}>", 20, "1d")],
            [rl(f"{AGENT_PREFIX}>", 50, "1d")],
        ]

        limits = UsageLimitService.get_effective_limits_for_roles(
            ["roleA", "roleB"], resource_path=f"{AGENT_PREFIX}LLMWrappingAgent.dev_agent"
        )

        assert len(limits) == 1
        assert limits[0].limit == 50


