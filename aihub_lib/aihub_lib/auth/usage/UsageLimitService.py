from __future__ import annotations

from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.auth.usage.usage_limit_models import (
    ResourceType,
    RoleUsageLimit,
    RoleUsageLimitStatus,
    UsageLimitPeriod,
    UsageStatus,
)
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

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
        if new_count == 1 or redis.call('TTL', KEYS[i]) < 0 then
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


class UsageLimitService:
    """
    Role-based usage limits with pattern matching.

    Patterns use dotted resource paths with wildcards:
    - ``*`` matches a single level
    - ``>`` matches one or more levels (must be last segment)

    All matching patterns are enforced independently. For the same pattern across roles,
    the highest limit (most permissive) wins. Different patterns are independent limits.
    Redis counters are keyed by the matched pattern, not the concrete resource path.
    """

    @staticmethod
    def build_resource_path(scope: str, resource_type: ResourceType, resource_class: str, resource_id: str) -> str:
        """Build a fully qualified resource path from its parts.

        >>> UsageLimitService.build_resource_path("aihub.user", ResourceType.AGENT, "MyAgent", "v1")
        'aihub.user.agent.MyAgent.v1'
        """
        return f"{scope}.{resource_type}.{resource_class}.{resource_id}"

    @staticmethod
    def _pattern_matches(pattern: str, concrete_path: str) -> bool:
        """Wildcard matching: ``*`` = single level, ``>`` = one or more trailing levels."""
        pattern_parts = pattern.split(".")
        concrete_parts = concrete_path.split(".")

        for i, part in enumerate(pattern_parts):
            if part == ">":
                if i != len(pattern_parts) - 1:
                    raise ValueError(f"Invalid pattern: '>' must be the last segment, got {pattern!r}")
                return i < len(concrete_parts)
            if i >= len(concrete_parts):
                return False
            if part != "*" and part != concrete_parts[i]:
                return False
        return len(pattern_parts) == len(concrete_parts)

    @staticmethod
    def _specificity(pattern: str) -> int:
        """Non-wildcard segment count — higher means more specific."""
        return sum(1 for segment in pattern.split(".") if segment not in ("*", ">"))

    @staticmethod
    def _build_redis_key(user_id: str, pattern: str, period: UsageLimitPeriod) -> str:
        if ":" in user_id or "\n" in user_id or "\r" in user_id:
            raise ValueError(f"Invalid user_id for Redis key: must not contain ':' or newlines, got {user_id!r}")
        return f"usage:calls:{user_id}:{pattern}:{period}"

    @staticmethod
    async def _resolve_reset_at(redis: Redis, key: str) -> datetime | None:
        """Derive the reset timestamp from the Redis TTL of a counter key."""
        ttl = await redis.ttl(key)
        if ttl <= 0:
            return None
        return datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=ttl)

    @staticmethod
    async def _build_limit_status(
        redis: Redis,
        effective_limit: RoleUsageLimit,
        key: str,
        current_count: int,
        *,
        post_increment: bool = False,
    ) -> RoleUsageLimitStatus:
        """Build a status snapshot for a single effective limit.

        After increment the count already includes the current call, so exceeded
        means strictly exceeding the limit (``>``).  Before increment (or when
        just reading) the counter hasn't been bumped yet, so hitting the limit
        exactly (``>=``) already means no more calls are allowed.
        """
        is_exceeded = (
            current_count > effective_limit.limit if post_increment else current_count >= effective_limit.limit
        )
        return RoleUsageLimitStatus(
            pattern=effective_limit.pattern,
            limit=effective_limit.limit,
            period=effective_limit.period,
            current_count=current_count,
            reset_at=await UsageLimitService._resolve_reset_at(redis, key),
            is_exceeded=is_exceeded,
        )

    @staticmethod
    @trace_fn
    def get_effective_limits_for_roles(
        role_names: list[str],
        resource_path: str | None = None,
    ) -> list[RoleUsageLimit]:
        """
        Resolve all effective usage limits from the user's roles.

        Empty list means unlimited. For identical patterns across roles the most permissive
        limit wins; different patterns are enforced independently.
        """
        from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity

        all_role_limits = RoleEntity.get_usage_limits_for_roles(role_names)

        if not any(role_limits for role_limits in all_role_limits):
            return []

        if resource_path is None:
            return UsageLimitService._most_permissive_limit(all_role_limits)

        return UsageLimitService._matching_limits_for_resource(all_role_limits, resource_path)

    @staticmethod
    def _is_more_permissive(candidate: RoleUsageLimit, existing: RoleUsageLimit) -> bool:
        """Higher limit wins; on tie, longer period wins."""
        if candidate.limit != existing.limit:
            return candidate.limit > existing.limit
        return UsageLimitPeriod(candidate.period).seconds > UsageLimitPeriod(existing.period).seconds

    @staticmethod
    def _most_permissive_limit(
        all_role_limits: list[list[RoleUsageLimit]],
    ) -> list[RoleUsageLimit]:
        """Without a resource path, return the single most permissive rule across all roles."""
        best: RoleUsageLimit | None = None

        for role_limits in all_role_limits:
            for role_limit in role_limits:
                if best is None or UsageLimitService._is_more_permissive(role_limit, best):
                    best = role_limit

        if best is None:
            return []
        return [RoleUsageLimit(pattern=best.pattern, limit=best.limit, period=best.period)]

    @staticmethod
    def _most_restrictive_per_role(
        role_limits: list[RoleUsageLimit],
        resource_path: str,
    ) -> dict[str, RoleUsageLimit]:
        """Within a single role, keep only the most restrictive limit per pattern."""
        best: dict[str, RoleUsageLimit] = {}
        for role_limit in role_limits:
            if not UsageLimitService._pattern_matches(role_limit.pattern, resource_path):
                continue
            if role_limit.pattern not in best or role_limit.limit < best[role_limit.pattern].limit:
                best[role_limit.pattern] = role_limit
        return best

    @staticmethod
    def _merge_across_roles(per_role_best: list[dict[str, RoleUsageLimit]]) -> list[RoleUsageLimit]:
        """Across roles, the most permissive limit wins for each pattern."""
        merged: dict[str, RoleUsageLimit] = {}
        for role_best in per_role_best:
            for pattern, role_limit in role_best.items():
                if pattern not in merged or UsageLimitService._is_more_permissive(role_limit, merged[pattern]):
                    merged[pattern] = role_limit
        return [
            RoleUsageLimit(pattern=role_limit.pattern, limit=role_limit.limit, period=role_limit.period)
            for role_limit in merged.values()
        ]

    @staticmethod
    def _matching_limits_for_resource(
        all_role_limits: list[list[RoleUsageLimit]],
        resource_path: str,
    ) -> list[RoleUsageLimit]:
        """Collect matching patterns with two-phase deduplication.

        1. **Within** a single role: duplicate patterns are reduced to the most
           restrictive (lowest limit) — the admin intended the tighter constraint.
        2. **Across** roles: the same pattern is resolved to the most permissive
           (highest limit) — roles grant capabilities.
        """
        per_role_best = [
            role_best
            for role_limits in all_role_limits
            if role_limits
            if (role_best := UsageLimitService._most_restrictive_per_role(role_limits, resource_path))
        ]

        if not per_role_best:
            return []

        return UsageLimitService._merge_across_roles(per_role_best)

    @staticmethod
    @trace_fn
    def get_effective_limit_for_roles(
        role_names: list[str],
        resource_path: str | None = None,
    ) -> RoleUsageLimit | None:
        """Return the most specific matching limit across all roles."""
        limits = UsageLimitService.get_effective_limits_for_roles(role_names, resource_path)
        if not limits:
            return None
        return max(limits, key=lambda effective_limit: UsageLimitService._specificity(effective_limit.pattern))

    @staticmethod
    @trace_fn
    async def get_usage_status(
        redis: Redis,
        user_id: str,
        role_names: list[str],
        resource_path: str | None = None,
    ) -> UsageStatus:
        """Get current usage status without incrementing any counter."""
        effective_limits = UsageLimitService.get_effective_limits_for_roles(role_names, resource_path)
        if not effective_limits:
            return UsageStatus(limits=[], is_exceeded=False)

        keys = [
            UsageLimitService._build_redis_key(user_id, effective_limit.pattern, effective_limit.period)
            for effective_limit in effective_limits
        ]
        raw_values = await redis.mget(keys)

        limit_statuses: list[RoleUsageLimitStatus] = []
        for effective_limit, key, raw_value in zip(effective_limits, keys, raw_values):
            current_count = int(raw_value) if raw_value else 0
            limit_statuses.append(
                await UsageLimitService._build_limit_status(redis, effective_limit, key, current_count)
            )

        return UsageStatus(
            limits=limit_statuses,
            is_exceeded=any(status.is_exceeded for status in limit_statuses),
        )

    @staticmethod
    @trace_fn
    async def check_and_increment(
        redis: Redis,
        user_id: str,
        role_names: list[str],
        resource_path: str | None = None,
    ) -> UsageStatus:
        """Atomically check all usage limits and increment all counters if none exceeded.

        Uses a single Lua script so the check-then-increment is atomic within Redis,
        preventing race conditions under concurrent requests.
        """
        effective_limits = UsageLimitService.get_effective_limits_for_roles(role_names, resource_path)
        if not effective_limits:
            return UsageStatus(limits=[], is_exceeded=False)

        keys = [UsageLimitService._build_redis_key(user_id, el.pattern, el.period) for el in effective_limits]
        # ARGV alternates: limit1, ttl1, limit2, ttl2, ...
        argv = []
        for el in effective_limits:
            argv.append(str(el.limit))
            argv.append(str(el.period.seconds))

        result = await redis.eval(_CHECK_AND_INCREMENT_SCRIPT, len(keys), *keys, *argv)
        exceeded_flag = int(result[0])
        counts = [int(result[i + 1]) for i in range(len(effective_limits))]
        post_increment = exceeded_flag == 0

        limit_statuses: list[RoleUsageLimitStatus] = []
        for el, key, count in zip(effective_limits, keys, counts):
            limit_statuses.append(
                await UsageLimitService._build_limit_status(redis, el, key, count, post_increment=post_increment)
            )

        return UsageStatus(
            limits=limit_statuses,
            is_exceeded=any(status.is_exceeded for status in limit_statuses),
        )

    @staticmethod
    @trace_fn
    async def check_and_raise(
        redis: Redis,
        user: UserIdentity,
        resource_type: ResourceType,
        resource_class: str,
        resource_id: str,
        locale: str = "en",
    ) -> UsageStatus:
        """Check usage limits, increment counters, and raise HTTP 429 if exceeded.

        Convenience wrapper combining ``check_and_increment`` with the HTTP error
        response so callers don't duplicate the raise logic.
        """
        from fastapi import HTTPException

        from aihub_lib.auth.usage.period_labels import build_exceeded_detail

        resource_path = UsageLimitService.build_resource_path("aihub.user", resource_type, resource_class, resource_id)
        usage_status = await UsageLimitService.check_and_increment(
            redis, user.id, user.roles, resource_path=resource_path
        )
        if usage_status.is_exceeded:
            raise HTTPException(
                status_code=429,
                detail=build_exceeded_detail(usage_status, locale=locale).model_dump(),
            )
        return usage_status
