from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field
from redis.asyncio import Redis

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity, RoleUsageLimit

logger = logging.getLogger(__name__)


class UsageLimitPeriod(StrEnum):
    """Supported usage limit periods."""

    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"
    ONE_MONTH = "1mo"

    @property
    def seconds(self) -> int:
        """Duration of this period in seconds."""
        match self:
            case UsageLimitPeriod.ONE_HOUR:
                return 3600
            case UsageLimitPeriod.ONE_DAY:
                return 86400
            case UsageLimitPeriod.SEVEN_DAYS:
                return 604800
            case UsageLimitPeriod.ONE_MONTH:
                return 2592000


class EffectiveLimit(BaseModel):
    """A single resolved limit: pattern + limit + period."""

    pattern: Annotated[str, Field(description="Dotted resource pattern with optional wildcards (* single, > multi)")]
    limit: Annotated[int, Field(ge=0, description="Maximum number of allowed calls in the period")]
    period: Annotated[UsageLimitPeriod, Field(description="Time window for the limit")]


class EffectiveLimitStatus(BaseModel):
    """Runtime status for one effective limit."""

    pattern: Annotated[str, Field(description="Dotted resource pattern with optional wildcards (* single, > multi)")]
    limit: Annotated[int, Field(ge=0, description="Maximum number of allowed calls in the period")]
    period: Annotated[UsageLimitPeriod, Field(description="Time window for the limit")]
    current_count: Annotated[int, Field(ge=0, description="Number of calls made in the current period")]
    reset_at: Annotated[datetime | None, Field(description="UTC timestamp when the counter resets")]
    is_exceeded: Annotated[bool, Field(description="Whether the limit has been reached or exceeded")]


class UsageStatus(BaseModel):
    """Current usage status for a user across all matching limits."""

    limits: Annotated[list[EffectiveLimitStatus], Field(description="Status of each applicable limit")]
    is_exceeded: Annotated[bool, Field(description="Whether any limit has been exceeded")]

    @property
    def limit(self) -> int | None:
        """Most restrictive limit value — the exceeded or closest-to-exceeded limit."""
        entry = self._most_restrictive
        return entry.limit if entry else None

    @property
    def period(self) -> UsageLimitPeriod | None:
        """Period of the most restrictive limit."""
        entry = self._most_restrictive
        return entry.period if entry else None

    @property
    def current_count(self) -> int:
        """Current count of the most restrictive limit."""
        entry = self._most_restrictive
        return entry.current_count if entry else 0

    @property
    def reset_at(self) -> datetime | None:
        """Reset timestamp of the most restrictive limit."""
        entry = self._most_restrictive
        return entry.reset_at if entry else None

    @property
    def _most_restrictive(self) -> EffectiveLimitStatus | None:
        """The exceeded limit (first found) or the one closest to being exceeded."""
        if not self.limits:
            return None
        for entry in self.limits:
            if entry.is_exceeded:
                return entry
        return max(self.limits, key=lambda e: e.current_count / e.limit if e.limit > 0 else 0)


class ResourceType(StrEnum):
    """Known resource type prefixes for usage limits."""

    AGENT = "agent"


_RESOURCE_PATH_PREFIX = "aihub.user"


class UsageLimitService:
    """
    Role-based usage limits with pattern matching.

    Patterns use dotted resource paths with wildcards:
    - ``*`` matches a single level
    - ``>`` matches one or more levels (must be last segment)

    All matching patterns are enforced independently. For the same pattern across roles,
    the highest limit (most permissive) wins. Different patterns are independent limits.
    Redis counters are keyed by the matched pattern, not the concrete resource path.

    Use :meth:`build_resource_path` to construct the full dotted path from parts.
    """

    @staticmethod
    def build_resource_path(resource_type: ResourceType, resource_class: str, resource_id: str) -> str:
        """Build a fully qualified resource path from its parts.

        >>> UsageLimitService.build_resource_path(ResourceType.AGENT, "MyAgent", "v1")
        'aihub.user.agent.MyAgent.v1'
        """
        return f"{_RESOURCE_PATH_PREFIX}.{resource_type}.{resource_class}.{resource_id}"

    @staticmethod
    def _pattern_matches(pattern: str, concrete_path: str) -> bool:
        """Wildcard matching: ``*`` = single level, ``>`` = one or more trailing levels."""
        pattern_parts = pattern.split(".")
        concrete_parts = concrete_path.split(".")

        for i, part in enumerate(pattern_parts):
            if part == ">":
                return i < len(concrete_parts)
            if i >= len(concrete_parts):
                return False
            if part != "*" and part != concrete_parts[i]:
                return False
        return len(pattern_parts) == len(concrete_parts)

    @staticmethod
    def _specificity(pattern: str) -> int:
        """Non-wildcard segment count — higher means more specific."""
        return sum(1 for p in pattern.split(".") if p not in ("*", ">"))

    @staticmethod
    def _build_redis_key(user_id: str, pattern: str, period: UsageLimitPeriod) -> str:
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
        effective_limit: EffectiveLimit,
        key: str,
        current_count: int,
        *,
        post_increment: bool = False,
    ) -> EffectiveLimitStatus:
        """Build a status snapshot for a single effective limit.

        After increment the count already includes the current call, so exceeded
        means strictly exceeding the limit (``>``).  Before increment (or when
        just reading) the counter hasn't been bumped yet, so hitting the limit
        exactly (``>=``) already means no more calls are allowed.
        """
        is_exceeded = (
            current_count > effective_limit.limit if post_increment else current_count >= effective_limit.limit
        )
        return EffectiveLimitStatus(
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
    ) -> list[EffectiveLimit]:
        """
        Resolve all effective usage limits from the user's roles.

        Empty list means unlimited. For identical patterns across roles the most permissive
        limit wins; different patterns are enforced independently.
        """
        all_role_limits = RoleEntity.get_usage_limits_for_roles(role_names)

        if not any(role_limits for role_limits in all_role_limits):
            return []

        if resource_path is None:
            return UsageLimitService._most_permissive_limit(all_role_limits)

        return UsageLimitService._matching_limits_for_resource(all_role_limits, resource_path)

    @staticmethod
    def _most_permissive_limit(
        all_role_limits: list[list[RoleUsageLimit]],
    ) -> list[EffectiveLimit]:
        """Without a resource path, return the single most permissive rule across all roles."""
        best: EffectiveLimit | None = None
        best_period_seconds = 0

        for role_limits in all_role_limits:
            for rl in role_limits:
                period_seconds = UsageLimitPeriod(rl.period).seconds
                if (
                    best is None
                    or rl.limit > best.limit
                    or (rl.limit == best.limit and period_seconds > best_period_seconds)
                ):
                    best = EffectiveLimit(pattern=rl.pattern, limit=rl.limit, period=rl.period)
                    best_period_seconds = period_seconds

        return [best] if best else []

    @staticmethod
    def _matching_limits_for_resource(
        all_role_limits: list[list[RoleUsageLimit]],
        resource_path: str,
    ) -> list[EffectiveLimit]:
        """Collect matching patterns with two-phase deduplication.

        1. **Within** a single role: duplicate patterns are reduced to the most
           restrictive (lowest limit) — the admin intended the tighter constraint.
        2. **Across** roles: the same pattern is resolved to the most permissive
           (highest limit) — roles grant capabilities.
        """
        # Phase 1: per-role dedup (most restrictive wins within a role)
        per_role_best: list[dict[str, RoleUsageLimit]] = []
        for role_limits in all_role_limits:
            if not role_limits:
                continue
            role_best: dict[str, RoleUsageLimit] = {}
            for rl in role_limits:
                if not UsageLimitService._pattern_matches(rl.pattern, resource_path):
                    continue
                if rl.pattern not in role_best or rl.limit < role_best[rl.pattern].limit:
                    role_best[rl.pattern] = rl
            if role_best:
                per_role_best.append(role_best)

        if not per_role_best:
            return []

        # Phase 2: cross-role merge (most permissive wins across roles)
        merged: dict[str, RoleUsageLimit] = {}
        for role_best in per_role_best:
            for pattern, rl in role_best.items():
                if pattern not in merged:
                    merged[pattern] = rl
                else:
                    existing = merged[pattern]
                    period_seconds = UsageLimitPeriod(rl.period).seconds
                    existing_period_seconds = UsageLimitPeriod(existing.period).seconds
                    if rl.limit > existing.limit or (
                        rl.limit == existing.limit and period_seconds > existing_period_seconds
                    ):
                        merged[pattern] = rl

        return [EffectiveLimit(pattern=rl.pattern, limit=rl.limit, period=rl.period) for rl in merged.values()]

    @staticmethod
    @trace_fn
    def get_effective_limit_for_roles(
        role_names: list[str],
        resource_path: str | None = None,
    ) -> tuple[int | None, UsageLimitPeriod | None, str | None]:
        """Legacy single-limit accessor — returns the most specific matching limit."""
        limits = UsageLimitService.get_effective_limits_for_roles(role_names, resource_path)
        if not limits:
            return None, None, None
        best = max(limits, key=lambda el: UsageLimitService._specificity(el.pattern))
        return best.limit, best.period, best.pattern

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

        limit_statuses: list[EffectiveLimitStatus] = []
        for effective_limit in effective_limits:
            key = UsageLimitService._build_redis_key(user_id, effective_limit.pattern, effective_limit.period)
            raw_count = await redis.get(key)
            current_count = int(raw_count) if raw_count else 0
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
        """Atomically check all usage limits and increment all counters if none exceeded."""
        effective_limits = UsageLimitService.get_effective_limits_for_roles(role_names, resource_path)
        if not effective_limits:
            return UsageStatus(limits=[], is_exceeded=False)

        checks = await UsageLimitService._read_all_counters(redis, user_id, effective_limits)
        any_exceeded = any(current_count >= el.limit for el, _, current_count in checks)

        logger.debug(f"Usage check: user={user_id}, limits={len(effective_limits)}, any_exceeded={any_exceeded}")

        if any_exceeded:
            return await UsageLimitService._build_status_from_checks(redis, checks, is_exceeded=True)

        return await UsageLimitService._increment_all_counters(redis, user_id, checks)

    @staticmethod
    async def _read_all_counters(
        redis: Redis,
        user_id: str,
        effective_limits: list[EffectiveLimit],
    ) -> list[tuple[EffectiveLimit, str, int]]:
        """Read current counter values for all effective limits."""
        checks: list[tuple[EffectiveLimit, str, int]] = []
        for effective_limit in effective_limits:
            key = UsageLimitService._build_redis_key(user_id, effective_limit.pattern, effective_limit.period)
            raw_count = await redis.get(key)
            current_count = int(raw_count) if raw_count else 0
            checks.append((effective_limit, key, current_count))
        return checks

    @staticmethod
    async def _build_status_from_checks(
        redis: Redis,
        checks: list[tuple[EffectiveLimit, str, int]],
        *,
        is_exceeded: bool,
    ) -> UsageStatus:
        """Build a UsageStatus from pre-read counter values."""
        limit_statuses = [
            await UsageLimitService._build_limit_status(redis, effective_limit, key, current_count)
            for effective_limit, key, current_count in checks
        ]
        return UsageStatus(limits=limit_statuses, is_exceeded=is_exceeded)

    @staticmethod
    async def _increment_all_counters(
        redis: Redis,
        user_id: str,
        checks: list[tuple[EffectiveLimit, str, int]],
    ) -> UsageStatus:
        """Increment all counters and return the resulting status."""
        limit_statuses: list[EffectiveLimitStatus] = []

        for effective_limit, key, _ in checks:
            ttl_seconds = effective_limit.period.seconds
            new_count = await redis.incr(key)
            logger.debug(
                f"Usage incremented: user={user_id}, key={key}, new_count={new_count}, limit={effective_limit.limit}"
            )

            if new_count == 1:
                await redis.expire(key, ttl_seconds)

            limit_statuses.append(
                await UsageLimitService._build_limit_status(redis, effective_limit, key, new_count, post_increment=True)
            )

        return UsageStatus(
            limits=limit_statuses,
            is_exceeded=any(status.is_exceeded for status in limit_statuses),
        )
