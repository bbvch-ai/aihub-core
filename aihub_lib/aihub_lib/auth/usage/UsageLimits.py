from __future__ import annotations

from redis.asyncio import Redis

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.auth.usage.RateLimitStore import CounterState, RateLimitStore
from aihub_lib.auth.usage.usage_limit_models import (
    USER_SCOPE,
    ResourceType,
    RoleUsageLimit,
    RoleUsageLimitStatus,
    UsageStatus,
)
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class UsageLimits:
    """
    Role-based usage limits with pattern matching.

    Patterns use dotted resource paths with wildcards:
    - ``*`` matches a single level
    - ``>`` matches one or more levels (must be last segment)

    All matching patterns are enforced independently. For the same pattern across roles,
    the highest limit (most permissive) wins. Different patterns are independent limits.
    Redis counters are keyed by the matched pattern, not the concrete resource path.
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    def _store_for_user(self, user_id: str) -> RateLimitStore:
        """Create a RateLimitStore scoped to a specific user."""
        return RateLimitStore(self._redis, user_id)

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
    def _build_limit_status(
        limit: RoleUsageLimit,
        counter: CounterState,
        *,
        post_increment: bool = False,
    ) -> RoleUsageLimitStatus:
        """Build a status snapshot for a single effective limit.

        After increment the count already includes the current call, so exceeded
        means strictly exceeding the limit (``>``).  Before increment (or when
        just reading) the counter hasn't been bumped yet, so hitting the limit
        exactly (``>=``) already means no more calls are allowed.
        """
        is_exceeded = counter.count > limit.limit if post_increment else counter.count >= limit.limit
        return RoleUsageLimitStatus(
            pattern=limit.pattern,
            limit=limit.limit,
            period=limit.period,
            current_count=counter.count,
            reset_at=counter.reset_at,
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

        # A role without limits means unlimited access — if any role grants unlimited, the user is unlimited
        if not all_role_limits or any(not role_limits for role_limits in all_role_limits):
            return []

        if resource_path is None:
            return UsageLimits._most_permissive_limit(all_role_limits)

        return UsageLimits._matching_limits_for_resource(all_role_limits, resource_path)

    @staticmethod
    def _most_permissive_limit(
        all_role_limits: list[list[RoleUsageLimit]],
    ) -> list[RoleUsageLimit]:
        """Without a resource path, return the single most permissive rule across all roles."""
        best: RoleUsageLimit | None = None
        for role_limits in all_role_limits:
            for limit in role_limits:
                if best is None or limit.limit > best.limit:
                    best = limit
        return [best] if best else []

    @staticmethod
    def _matching_limits_for_resource(
        all_role_limits: list[list[RoleUsageLimit]],
        resource_path: str,
    ) -> list[RoleUsageLimit]:
        """Collect matching limits, taking the most permissive (highest) per (pattern, period).

        RoleEntity.clean() guarantees no duplicate (pattern, period) within a role,
        so we only need to merge across roles — highest limit wins.
        """
        merged: dict[tuple[str, str], RoleUsageLimit] = {}
        for role_limits in all_role_limits:
            for limit in role_limits:
                if not UsageLimits._pattern_matches(limit.pattern, resource_path):
                    continue
                key = (limit.pattern, limit.period)
                if key not in merged or limit.limit > merged[key].limit:
                    merged[key] = limit
        return list(merged.values())

    @staticmethod
    @trace_fn
    def get_effective_limit_for_roles(
        role_names: list[str],
        resource_path: str | None = None,
    ) -> RoleUsageLimit | None:
        """Return the most specific matching limit across all roles."""
        limits = UsageLimits.get_effective_limits_for_roles(role_names, resource_path)
        if not limits:
            return None
        return max(limits, key=lambda effective_limit: UsageLimits._specificity(effective_limit.pattern))

    @trace_fn
    async def get_usage_status(
        self,
        user_id: str,
        role_names: list[str],
        resource_path: str | None = None,
    ) -> UsageStatus:
        """Get current usage status without incrementing any counter."""
        effective_limits = self.get_effective_limits_for_roles(role_names, resource_path)
        if not effective_limits:
            return UsageStatus(limits=[], is_exceeded=False)

        store = self._store_for_user(user_id)
        counters: list[CounterState] = await store.get_counts(effective_limits)

        limit_statuses = [
            self._build_limit_status(limit, counter) for limit, counter in zip(effective_limits, counters)
        ]

        return UsageStatus(
            limits=limit_statuses,
            is_exceeded=any(status.is_exceeded for status in limit_statuses),
        )

    @trace_fn
    async def check_and_increment(
        self,
        user_id: str,
        role_names: list[str],
        resource_path: str | None = None,
    ) -> UsageStatus:
        """Atomically check all usage limits and increment all counters if none exceeded.

        Uses a single Lua script so the check-then-increment is atomic within Redis,
        preventing race conditions under concurrent requests.
        """
        effective_limits = self.get_effective_limits_for_roles(role_names, resource_path)
        if not effective_limits:
            return UsageStatus(limits=[], is_exceeded=False)

        store = self._store_for_user(user_id)
        incremented, counters = await store.check_and_increment(effective_limits)

        limit_statuses = [
            self._build_limit_status(limit, counter, post_increment=incremented)
            for limit, counter in zip(effective_limits, counters)
        ]

        return UsageStatus(
            limits=limit_statuses,
            is_exceeded=any(status.is_exceeded for status in limit_statuses),
        )

    @trace_fn
    async def check_and_raise(
        self,
        user: UserIdentity,
        resource_type: ResourceType,
        resource_class: str,
        resource_id: str,
        locale: str | None = None,
    ) -> UsageStatus:
        """Check usage limits, increment counters, and raise HTTP 429 if exceeded.

        Convenience wrapper combining ``check_and_increment`` with the HTTP error
        response so callers don't duplicate the raise logic.
        """
        from fastapi import HTTPException

        from aihub_lib.auth.usage.UsageLimitMessages import UsageLimitMessages

        resource_path = f"{USER_SCOPE}.{resource_type}.{resource_class}.{resource_id}"
        usage_status = await self.check_and_increment(user.id, user.roles, resource_path=resource_path)
        if usage_status.is_exceeded:
            effective_locale = locale or LocaleHandler.DEFAULT_LOCALE
            raise HTTPException(
                status_code=429,
                detail=UsageLimitMessages.build_exceeded_detail(usage_status, locale=effective_locale).model_dump(),
            )
        return usage_status
