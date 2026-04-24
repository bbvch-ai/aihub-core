from unittest.mock import AsyncMock

import pytest

from swiss_ai_hub.core.auth.usage.rate_limit_store import RateLimitStore
from swiss_ai_hub.core.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod


def rl(pattern: str, limit: int, period: str) -> RoleUsageLimit:
    """Shorthand factory for test readability."""
    return RoleUsageLimit(pattern=pattern, limit=limit, period=period)


TEST_TENANT_ID = "test-tenant"


class TestValidateKeySegment:
    """Tests for RateLimitStore._validate_key_segment"""

    def test_valid_values(self):
        RateLimitStore._validate_key_segment("user123", "user_id")
        RateLimitStore._validate_key_segment("user@example.com", "user_id")
        RateLimitStore._validate_key_segment("123-456-789", "tenant_id")

    def test_empty_value_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            RateLimitStore._validate_key_segment("", "user_id")

    def test_value_with_colon_raises(self):
        with pytest.raises(ValueError, match="must not be empty or contain"):
            RateLimitStore._validate_key_segment("user:123", "user_id")

    def test_value_with_newline_raises(self):
        with pytest.raises(ValueError, match="must not be empty or contain"):
            RateLimitStore._validate_key_segment("user\n123", "tenant_id")

    def test_value_with_carriage_return_raises(self):
        with pytest.raises(ValueError, match="must not be empty or contain"):
            RateLimitStore._validate_key_segment("user\r123", "tenant_id")


class TestBuildKey:
    """Tests for RateLimitStore._build_key"""

    def test_builds_key_with_default_prefix(self):
        redis = AsyncMock()
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)
        key = store._build_key("aihub.user.agent.>", UsageLimitPeriod.ONE_DAY)
        assert key == f"usage:calls:{TEST_TENANT_ID}:user123:aihub.user.agent.>:1d"

    def test_builds_key_with_custom_prefix(self):
        redis = AsyncMock()
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID, key_prefix="custom:prefix")
        key = store._build_key("aihub.user.agent.>", UsageLimitPeriod.ONE_HOUR)
        assert key == f"custom:prefix:{TEST_TENANT_ID}:user123:aihub.user.agent.>:1h"

    def test_validates_user_id_in_constructor(self):
        redis = AsyncMock()
        with pytest.raises(ValueError):
            RateLimitStore(redis, "user:123", TEST_TENANT_ID)

    def test_validates_tenant_id_in_constructor(self):
        redis = AsyncMock()
        with pytest.raises(ValueError):
            RateLimitStore(redis, "user123", "tenant:bad")


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
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)

        result = await store.get_counts([])

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_counts_and_reset_times(self):
        redis = AsyncMock()
        redis.fcall.return_value = [42, 3600, 5, 1800]
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 10, "1h"),
        ]
        result = await store.get_counts(limits)

        assert len(result) == 2
        assert result[0][0] == 42
        assert result[0][1] is not None
        assert result[1][0] == 5
        assert result[1][1] is not None

    @pytest.mark.asyncio
    async def test_handles_missing_keys(self):
        redis = AsyncMock()
        redis.fcall.return_value = [0, -1, 5, 1800]
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 10, "1h"),
        ]
        result = await store.get_counts(limits)

        assert result[0][0] == 0
        assert result[0][1] is None
        assert result[1][0] == 5
        assert result[1][1] is not None


class TestCheckAndIncrement:
    """Tests for RateLimitStore.check_and_increment"""

    @pytest.mark.asyncio
    async def test_empty_limits_returns_true_and_empty_list(self):
        redis = AsyncMock()
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)

        incremented, counts = await store.check_and_increment([])

        assert incremented is True
        assert counts == []

    @pytest.mark.asyncio
    async def test_increments_when_not_exceeded(self):
        redis = AsyncMock()
        redis.fcall.return_value = [0, 6, 80000, 4, 3600]
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 20, "1h"),
        ]
        incremented, counts = await store.check_and_increment(limits)

        assert incremented is True
        assert len(counts) == 2
        assert counts[0][0] == 6
        assert counts[1][0] == 4

    @pytest.mark.asyncio
    async def test_does_not_increment_when_exceeded(self):
        redis = AsyncMock()
        redis.fcall.return_value = [1, 5, 1800, 10, 3600]
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)

        limits = [
            rl("aihub.user.agent.>", 100, "1d"),
            rl("aihub.user.agent.MyAgent.>", 10, "1h"),
        ]
        incremented, counts = await store.check_and_increment(limits)

        assert incremented is False
        assert len(counts) == 2
        assert counts[0][0] == 5
        assert counts[1][0] == 10

    @pytest.mark.asyncio
    async def test_passes_correct_arguments_to_fcall(self):
        redis = AsyncMock()
        redis.fcall.return_value = [0, 1, 86400]
        store = RateLimitStore(redis, "user123", TEST_TENANT_ID)

        limits = [rl("aihub.user.agent.>", 100, "1d")]
        await store.check_and_increment(limits)

        redis.fcall.assert_called_once()
        call_args = redis.fcall.call_args[0]
        assert call_args[0] == "aihub_check_and_increment"
        assert call_args[1] == 1  # num_keys
        assert call_args[2] == f"usage:calls:{TEST_TENANT_ID}:user123:aihub.user.agent.>:1d"
        assert "100" in call_args
        assert "86400" in call_args


class TestParseLuaResult:
    """Tests for RateLimitStore._parse_lua_result"""

    def test_empty_input(self):
        result = RateLimitStore._parse_lua_result([])
        assert result == []

    def test_single_entry(self):
        result = RateLimitStore._parse_lua_result([42, 3600])
        assert len(result) == 1
        assert result[0][0] == 42
        assert result[0][1] is not None

    def test_negative_ttl_gives_none_reset(self):
        result = RateLimitStore._parse_lua_result([5, -1])
        assert result[0][0] == 5
        assert result[0][1] is None
