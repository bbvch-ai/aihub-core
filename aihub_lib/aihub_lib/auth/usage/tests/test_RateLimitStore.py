from unittest.mock import AsyncMock

import pytest

from aihub_lib.auth.usage.RateLimitStore import RateLimitStore
from aihub_lib.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod


def rl(pattern: str, limit: int, period: str) -> RoleUsageLimit:
    """Shorthand factory for test readability."""
    return RoleUsageLimit(pattern=pattern, limit=limit, period=period)


class TestValidateUserId:
    """Tests for RateLimitStore._validate_user_id"""

    def test_valid_user_id(self):
        RateLimitStore._validate_user_id("user123")
        RateLimitStore._validate_user_id("user@example.com")
        RateLimitStore._validate_user_id("123-456-789")

    def test_empty_user_id_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            RateLimitStore._validate_user_id("")

    def test_user_id_with_colon_raises(self):
        with pytest.raises(ValueError, match="must not be empty or contain"):
            RateLimitStore._validate_user_id("user:123")

    def test_user_id_with_newline_raises(self):
        with pytest.raises(ValueError, match="must not be empty or contain"):
            RateLimitStore._validate_user_id("user\n123")

    def test_user_id_with_carriage_return_raises(self):
        with pytest.raises(ValueError, match="must not be empty or contain"):
            RateLimitStore._validate_user_id("user\r123")


class TestBuildKey:
    """Tests for RateLimitStore._build_key"""

    def test_builds_key_with_default_prefix(self):
        redis = AsyncMock()
        store = RateLimitStore(redis)
        key = store._build_key("user123", "aihub.user.agent.>", UsageLimitPeriod.ONE_DAY)
        assert key == "usage:calls:user123:aihub.user.agent.>:1d"

    def test_builds_key_with_custom_prefix(self):
        redis = AsyncMock()
        store = RateLimitStore(redis, key_prefix="custom:prefix")
        key = store._build_key("user123", "aihub.user.agent.>", UsageLimitPeriod.ONE_HOUR)
        assert key == "custom:prefix:user123:aihub.user.agent.>:1h"

    def test_validates_user_id(self):
        redis = AsyncMock()
        store = RateLimitStore(redis)
        with pytest.raises(ValueError):
            store._build_key("user:123", "pattern", UsageLimitPeriod.ONE_DAY)


class TestTtlToResetAt:
    """Tests for RateLimitStore._ttl_to_reset_at"""

    def test_zero_ttl_returns_none(self):
        assert RateLimitStore._ttl_to_reset_at(0) is None

    def test_negative_ttl_returns_none(self):
        assert RateLimitStore._ttl_to_reset_at(-1) is None

    def test_positive_ttl_returns_future_datetime(self):
        reset_at = RateLimitStore._ttl_to_reset_at(3600)
        assert reset_at is not None
        assert reset_at.microsecond == 0


class TestGetCounts:
    """Tests for RateLimitStore.get_counts"""

    @pytest.mark.asyncio
    async def test_empty_limits_returns_empty_list(self):
        redis = AsyncMock()
        store = RateLimitStore(redis)

        result = await store.get_counts("user123", [])

        assert result == []
        redis.mget.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_counts_and_reset_times(self):
        redis = AsyncMock()
        redis.mget.return_value = [b"42", b"5"]
        redis.ttl.side_effect = [3600, 1800]
        store = RateLimitStore(redis)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 10, "1h"),
        ]
        result = await store.get_counts("user123", limits)

        assert len(result) == 2
        assert result[0][0] == 42
        assert result[0][1] is not None
        assert result[1][0] == 5
        assert result[1][1] is not None

    @pytest.mark.asyncio
    async def test_handles_missing_keys(self):
        redis = AsyncMock()
        redis.mget.return_value = [None, b"5"]
        redis.ttl.side_effect = [-1, 1800]
        store = RateLimitStore(redis)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 10, "1h"),
        ]
        result = await store.get_counts("user123", limits)

        assert result[0][0] == 0
        assert result[0][1] is None
        assert result[1][0] == 5
        assert result[1][1] is not None


class TestCheckAndIncrement:
    """Tests for RateLimitStore.check_and_increment"""

    @pytest.mark.asyncio
    async def test_empty_limits_returns_true_and_empty_list(self):
        redis = AsyncMock()
        store = RateLimitStore(redis)

        incremented, counts = await store.check_and_increment("user123", [])

        assert incremented is True
        assert counts == []
        redis.eval.assert_not_called()

    @pytest.mark.asyncio
    async def test_increments_when_not_exceeded(self):
        redis = AsyncMock()
        redis.eval.return_value = [0, 6, 4]  # exceeded_flag=0, count1=6, count2=4
        redis.ttl.return_value = 80000
        store = RateLimitStore(redis)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 20, "1h"),
        ]
        incremented, counts = await store.check_and_increment("user123", limits)

        assert incremented is True
        assert len(counts) == 2
        assert counts[0][0] == 6
        assert counts[1][0] == 4
        redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_increment_when_exceeded(self):
        redis = AsyncMock()
        redis.eval.return_value = [1, 5, 10]  # exceeded_flag=1, count1=5, count2=10
        redis.ttl.return_value = 1800
        store = RateLimitStore(redis)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 10, "1h"),
        ]
        incremented, counts = await store.check_and_increment("user123", limits)

        assert incremented is False
        assert len(counts) == 2
        assert counts[0][0] == 5
        assert counts[1][0] == 10

    @pytest.mark.asyncio
    async def test_passes_correct_arguments_to_lua_script(self):
        redis = AsyncMock()
        redis.eval.return_value = [0, 1]
        redis.ttl.return_value = 3600
        store = RateLimitStore(redis)

        limits = [rl("aihub.user.agent.>", 100, "1d")]
        await store.check_and_increment("user123", limits)

        call_args = redis.eval.call_args
        # Check script, num_keys, keys, and argv
        assert call_args[0][1] == 1  # num_keys
        assert "usage:calls:user123:aihub.user.agent.>:1d" in call_args[0][2]  # key
        assert "100" in call_args[0]  # limit
        assert "86400" in call_args[0]  # ttl for 1d
