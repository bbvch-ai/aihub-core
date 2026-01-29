from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from pydantic import BaseModel
from redis.asyncio import Redis

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity

logger = logging.getLogger(__name__)

PATTERN_PREFIX = "aihub.user.agent."


class UsageLimitPeriod(StrEnum):
    """Supported usage limit periods."""

    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"
    ONE_MONTH = "1mo"


PERIOD_SECONDS: dict[str, int] = {
    UsageLimitPeriod.ONE_HOUR: 3600,
    UsageLimitPeriod.ONE_DAY: 86400,
    UsageLimitPeriod.SEVEN_DAYS: 604800,
    UsageLimitPeriod.ONE_MONTH: 2592000,
}


class EffectiveLimit(BaseModel):
    """A single resolved limit: pattern + limit + period."""

    pattern: str
    limit: int
    period: str


class EffectiveLimitStatus(BaseModel):
    """Runtime status for one effective limit."""

    pattern: str
    limit: int
    period: str
    current_count: int
    reset_at: datetime | None
    is_exceeded: bool


class UsageStatus(BaseModel):
    """Current usage status for a user across all matching limits."""

    limits: list[EffectiveLimitStatus]
    is_exceeded: bool

    @property
    def limit(self) -> int | None:
        """Most restrictive limit value (for backward compat). Returns the exceeded or closest-to-exceeded limit."""
        entry = self._most_restrictive
        return entry.limit if entry else None

    @property
    def period(self) -> str | None:
        entry = self._most_restrictive
        return entry.period if entry else None

    @property
    def current_count(self) -> int:
        entry = self._most_restrictive
        return entry.current_count if entry else 0

    @property
    def reset_at(self) -> datetime | None:
        entry = self._most_restrictive
        return entry.reset_at if entry else None

    @property
    def _most_restrictive(self) -> EffectiveLimitStatus | None:
        """Return the exceeded limit (first one) or the one closest to being exceeded."""
        if not self.limits:
            return None
        for entry in self.limits:
            if entry.is_exceeded:
                return entry
        # Return closest to exceeded (highest current_count / limit ratio)
        return max(self.limits, key=lambda e: e.current_count / e.limit if e.limit > 0 else 0)


class UsageLimitService:
    """
    Service for managing role-based usage limits with pattern matching.

    Patterns use NATS-style wildcards:
    - `*` matches a single level
    - `>` matches one or more levels (must be last segment)

    The implicit prefix `aihub.user.agent.` is prepended for matching but not stored.

    All matching patterns are enforced independently. For the same pattern across roles,
    the highest limit (most permissive) wins. Different patterns are independent limits.
    Redis counters are keyed by the matched pattern, not the concrete agent path.
    """

    @staticmethod
    def _pattern_matches(pattern: str, concrete_path: str) -> bool:
        """Check if a NATS-style pattern matches a concrete path. Both must include the full prefix."""
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
        """Count non-wildcard segments as a measure of specificity."""
        parts = pattern.split(".")
        return sum(1 for p in parts if p not in ("*", ">"))

    @staticmethod
    def _build_redis_key(user_id: str, pattern: str, period: str) -> str:
        """Build the Redis key for a user's usage counter."""
        return f"usage:agent_calls:{user_id}:{pattern}:{period}"

    @staticmethod
    @trace_fn
    def get_effective_limits_for_roles(
        role_names: list[str], agent_path: str | None = None
    ) -> list[EffectiveLimit]:
        """
        Determine all effective usage limits from all user roles.

        Returns a list of EffectiveLimit — all matching limits deduplicated by pattern
        (highest limit wins across roles for the same pattern). Empty list = unlimited.

        Resolution:
        1. Load usage_limits per role
        2. If no role has any usage_limits → empty (unlimited)
        3. Collect all matching (pattern, limit, period) tuples across all roles
        4. For the same pattern: take the highest limit (most permissive across roles)
        5. Different patterns are independent limits
        """
        all_role_limits = RoleEntity.get_usage_limits_for_roles(role_names)

        if not any(role_limits for role_limits in all_role_limits):
            return []

        if agent_path is None:
            # No agent_path: return the single most permissive rule across all roles
            best: EffectiveLimit | None = None
            best_period_seconds = 0
            for role_limits in all_role_limits:
                for pattern, limit, period in role_limits:
                    ps = PERIOD_SECONDS.get(period, 0)
                    if best is None or limit > best.limit or (limit == best.limit and ps > best_period_seconds):
                        best = EffectiveLimit(pattern=pattern, limit=limit, period=period)
                        best_period_seconds = ps
            return [best] if best else []

        full_agent_path = PATTERN_PREFIX + agent_path

        # Collect all matching patterns across all roles, grouped by pattern
        # Key: pattern string → list of (limit, period) from each role
        pattern_candidates: dict[str, list[tuple[int, str]]] = {}

        for role_limits in all_role_limits:
            if not role_limits:
                continue
            for pattern, limit, period in role_limits:
                if UsageLimitService._pattern_matches(pattern, full_agent_path):
                    pattern_candidates.setdefault(pattern, []).append((limit, period))

        if not pattern_candidates:
            return []

        # For each pattern, pick the highest limit across roles
        effective: list[EffectiveLimit] = []
        for pattern, candidates in pattern_candidates.items():
            best_limit = -1
            best_period = ""
            best_ps = 0
            for limit, period in candidates:
                ps = PERIOD_SECONDS.get(period, 0)
                if limit > best_limit or (limit == best_limit and ps > best_ps):
                    best_limit = limit
                    best_period = period
                    best_ps = ps
            effective.append(EffectiveLimit(pattern=pattern, limit=best_limit, period=best_period))

        return effective

    @staticmethod
    @trace_fn
    def get_effective_limit_for_roles(
        role_names: list[str], agent_path: str | None = None
    ) -> tuple[int | None, str | None, str | None]:
        """
        Legacy method: returns the single most specific limit.

        Kept for backward compatibility. Prefers the most specific pattern.
        """
        limits = UsageLimitService.get_effective_limits_for_roles(role_names, agent_path)
        if not limits:
            return None, None, None
        # Pick the most specific
        best = max(limits, key=lambda el: UsageLimitService._specificity(el.pattern))
        return best.limit, best.period, best.pattern

    @staticmethod
    @trace_fn
    async def get_usage_status(
        redis: Redis, user_id: str, role_names: list[str], agent_path: str | None = None
    ) -> UsageStatus:
        """Get current usage status without incrementing any counter."""
        effective_limits = UsageLimitService.get_effective_limits_for_roles(role_names, agent_path)

        if not effective_limits:
            return UsageStatus(limits=[], is_exceeded=False)

        limit_statuses: list[EffectiveLimitStatus] = []
        any_exceeded = False

        for el in effective_limits:
            key = UsageLimitService._build_redis_key(user_id, el.pattern, el.period)
            raw_count = await redis.get(key)
            current_count = int(raw_count) if raw_count else 0

            ttl = await redis.ttl(key)
            reset_at = None
            if ttl > 0:
                reset_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=ttl)

            exceeded = current_count >= el.limit
            if exceeded:
                any_exceeded = True

            limit_statuses.append(
                EffectiveLimitStatus(
                    pattern=el.pattern,
                    limit=el.limit,
                    period=el.period,
                    current_count=current_count,
                    reset_at=reset_at,
                    is_exceeded=exceeded,
                )
            )

        return UsageStatus(limits=limit_statuses, is_exceeded=any_exceeded)

    @staticmethod
    @trace_fn
    async def check_and_increment(
        redis: Redis, user_id: str, role_names: list[str], agent_path: str | None = None
    ) -> UsageStatus:
        """Atomically check all usage limits and increment all counters if none exceeded."""
        effective_limits = UsageLimitService.get_effective_limits_for_roles(role_names, agent_path)

        if not effective_limits:
            return UsageStatus(limits=[], is_exceeded=False)

        # Phase 1: Check all counters
        checks: list[tuple[EffectiveLimit, str, int]] = []
        any_exceeded = False

        for el in effective_limits:
            key = UsageLimitService._build_redis_key(user_id, el.pattern, el.period)
            raw_count = await redis.get(key)
            current_count = int(raw_count) if raw_count else 0
            checks.append((el, key, current_count))
            if current_count >= el.limit:
                any_exceeded = True

        logger.debug(
            f"Usage check: user={user_id}, limits={len(effective_limits)}, any_exceeded={any_exceeded}"
        )

        # Phase 2: If any exceeded, return without incrementing
        if any_exceeded:
            limit_statuses: list[EffectiveLimitStatus] = []
            for el, key, current_count in checks:
                ttl = await redis.ttl(key)
                reset_at = None
                if ttl > 0:
                    reset_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=ttl)
                limit_statuses.append(
                    EffectiveLimitStatus(
                        pattern=el.pattern,
                        limit=el.limit,
                        period=el.period,
                        current_count=current_count,
                        reset_at=reset_at,
                        is_exceeded=current_count >= el.limit,
                    )
                )
            return UsageStatus(limits=limit_statuses, is_exceeded=True)

        # Phase 3: Increment ALL counters
        limit_statuses = []
        for el, key, _ in checks:
            ttl_seconds = PERIOD_SECONDS.get(el.period, 86400)
            new_count = await redis.incr(key)
            logger.debug(f"Usage incremented: user={user_id}, key={key}, new_count={new_count}, limit={el.limit}")

            if new_count == 1:
                await redis.expire(key, ttl_seconds)

            ttl = await redis.ttl(key)
            reset_at = None
            if ttl > 0:
                reset_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=ttl)

            limit_statuses.append(
                EffectiveLimitStatus(
                    pattern=el.pattern,
                    limit=el.limit,
                    period=el.period,
                    current_count=new_count,
                    reset_at=reset_at,
                    is_exceeded=new_count > el.limit,
                )
            )

        return UsageStatus(
            limits=limit_statuses,
            is_exceeded=any(ls.is_exceeded for ls in limit_statuses),
        )
