from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from aihub_lib.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod

_CHECK_AND_INCREMENT_SCRIPT = """
-- Lua script that atomically checks all limits and increments all counters
-- only if none are exceeded. Returns an array of current counts.
--
-- KEYS: Redis counter keys (one per limit)
-- ARGV: For each key i: ARGV[2*i - 1] = limit, ARGV[2*i] = ttl_seconds
--
-- Return format: {exceeded_flag, count1, count2, ...}
--   exceeded_flag = 1 if any limit is at or above its max, 0 otherwise

local n = #KEYS
local counts = {}
local exceeded = 0

-- Phase 1: read all counters and check limits
for i = 1, n do
    local raw = redis.call('GET', KEYS[i])
    local count = raw and tonumber(raw) or 0
    counts[i] = count
    local limit = tonumber(ARGV[2 * i - 1])
    if count >= limit then
        exceeded = 1
    end
end

-- Phase 2: increment all counters only if none exceeded
if exceeded == 0 then
    for i = 1, n do
        local ttl = tonumber(ARGV[2 * i])
        local new_count = redis.call('INCR', KEYS[i])
        if new_count == 1 or redis.call('TTL', KEYS[i]) <= 0 then
            redis.call('EXPIRE', KEYS[i], ttl)
        end
        counts[i] = new_count
    end
end

-- Return exceeded flag followed by all counts
local result = {exceeded}
for i = 1, n do
    result[i + 1] = counts[i]
end
return result
"""


class RateLimitStore:
    """Redis-backed store for rate limit counters."""

    def __init__(self, redis: Redis, key_prefix: str = "usage:calls"):
        self.redis = redis
        self.key_prefix = key_prefix

    @staticmethod
    def _validate_user_id(user_id: str) -> None:
        """Validate user_id contains no characters that could cause Redis key injection."""
        if not user_id or ":" in user_id or "\n" in user_id or "\r" in user_id:
            raise ValueError(f"Invalid user_id for Redis: must not be empty or contain ':'/newlines, got {user_id!r}")

    def _build_key(self, user_id: str, pattern: str, period: UsageLimitPeriod) -> str:
        """Build a Redis key for a rate limit counter."""
        self._validate_user_id(user_id)
        return f"{self.key_prefix}:{user_id}:{pattern}:{period}"

    @staticmethod
    def _ttl_to_reset_at(ttl: int) -> datetime | None:
        """Convert a TTL value to a reset timestamp."""
        if ttl <= 0:
            return None
        return datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=ttl)

    async def _batch_resolve_reset_at(self, keys: list[str]) -> list[datetime | None]:
        """Batch fetch TTLs for multiple keys and convert to reset timestamps."""
        if not keys:
            return []
        ttls = await asyncio.gather(*[self.redis.ttl(key) for key in keys])
        return [self._ttl_to_reset_at(ttl) for ttl in ttls]

    async def get_counts(self, user_id: str, limits: list[RoleUsageLimit]) -> list[tuple[int, datetime | None]]:
        """Read current counter values and TTLs (no increment)."""
        if not limits:
            return []

        keys = [self._build_key(user_id, limit.pattern, limit.period) for limit in limits]
        raw_values = await self.redis.mget(keys)
        reset_ats = await self._batch_resolve_reset_at(keys)

        return [(int(raw_value) if raw_value else 0, reset_at) for raw_value, reset_at in zip(raw_values, reset_ats)]

    async def check_and_increment(
        self, user_id: str, limits: list[RoleUsageLimit]
    ) -> tuple[bool, list[tuple[int, datetime | None]]]:
        """Atomically check all limits and increment all counters if none exceeded.

        Uses a single Lua script so the check-then-increment is atomic within Redis,
        preventing race conditions under concurrent requests.
        """
        if not limits:
            return True, []

        keys = [self._build_key(user_id, limit.pattern, limit.period) for limit in limits]
        # ARGV alternates: limit1, ttl1, limit2, ttl2, ...
        argv: list[str] = []
        for limit in limits:
            argv.append(str(limit.limit))
            argv.append(str(limit.period.seconds))

        result = await self.redis.eval(_CHECK_AND_INCREMENT_SCRIPT, len(keys), *keys, *argv)
        exceeded_flag = int(result[0])
        counts = [int(count) for count in result[1:]]
        incremented = exceeded_flag == 0

        reset_ats = await self._batch_resolve_reset_at(keys)

        return incremented, list(zip(counts, reset_ats))
