from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import NamedTuple

from redis.asyncio import Redis

from aihub_lib.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod

logger = logging.getLogger(__name__)


class CounterState(NamedTuple):
    """Current value and expiry of a single rate-limit counter."""

    count: int
    reset_at: datetime | None


_LUA_DIR = Path(__file__).parent / "lua"
_CHECK_AND_INCREMENT_LUA = (_LUA_DIR / "check_and_increment.lua").read_text()
_GET_COUNTS_LUA = (_LUA_DIR / "get_counts.lua").read_text()


class RateLimitStore:
    """Redis-backed store for rate limit counters."""

    _functions_registered: bool = False

    def __init__(self, redis: Redis, user_id: str, key_prefix: str = "usage:calls"):
        self._validate_user_id(user_id)
        self.redis = redis
        self.user_id = user_id
        self.key_prefix = key_prefix

    @staticmethod
    def _validate_user_id(user_id: str) -> None:
        """Validate user_id contains no characters that could cause Redis key injection."""
        if not user_id or ":" in user_id or "\n" in user_id or "\r" in user_id:
            raise ValueError(f"Invalid user_id for Redis: must not be empty or contain ':'/newlines, got {user_id!r}")

    def _build_key(self, pattern: str, period: UsageLimitPeriod) -> str:
        """Build a Redis key for a rate limit counter."""
        return f"{self.key_prefix}:{self.user_id}:{pattern}:{period}"

    @staticmethod
    def _ttl_to_reset_at(ttl: int) -> datetime | None:
        """Convert a TTL value to a reset timestamp."""
        if ttl <= 0:
            return None
        return datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=ttl)

    @staticmethod
    def _parse_lua_result(raw_values: list[int]) -> list[CounterState]:
        """Parse interleaved [count1, ttl1, count2, ttl2, ...] into CounterState list."""
        result: list[CounterState] = []
        for i in range(0, len(raw_values), 2):
            count = int(raw_values[i])
            ttl = int(raw_values[i + 1])
            reset_at = RateLimitStore._ttl_to_reset_at(ttl)
            result.append(CounterState(count, reset_at))
        return result

    async def _register_functions(self) -> None:
        """Register Lua functions on first use. Called once per process lifetime."""
        if RateLimitStore._functions_registered:
            return
        await self.redis.function_load(_CHECK_AND_INCREMENT_LUA, replace=True)
        await self.redis.function_load(_GET_COUNTS_LUA, replace=True)
        RateLimitStore._functions_registered = True

    async def get_counts(self, limits: list[RoleUsageLimit]) -> list[CounterState]:
        """Read current counter values and TTLs atomically (no increment)."""
        if not limits:
            return []

        keys = [self._build_key(limit.pattern, limit.period) for limit in limits]

        await self._register_functions()
        result = await self.redis.fcall("aihub_get_counts", len(keys), *keys)

        return self._parse_lua_result(result)

    async def check_and_increment(self, limits: list[RoleUsageLimit]) -> tuple[bool, list[CounterState]]:
        """Atomically check all limits and increment all counters if none exceeded.

        Uses a single Lua script so the check-then-increment is atomic within Redis,
        preventing race conditions under concurrent requests.
        """
        if not limits:
            return True, []

        keys = [self._build_key(limit.pattern, limit.period) for limit in limits]
        # Lua expects interleaved args: [limit1, ttl1, limit2, ttl2, ...]
        args: list[str] = []
        for limit in limits:
            args.append(str(limit.limit))
            args.append(str(limit.period.seconds))

        await self._register_functions()
        result = await self.redis.fcall("aihub_check_and_increment", len(keys), *keys, *args)

        was_exceeded = bool(result[0])
        incremented = not was_exceeded

        counts_and_resets = self._parse_lua_result(result[1:])
        return incremented, counts_and_resets
