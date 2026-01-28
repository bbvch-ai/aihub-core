import re
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import HTTPException
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity


class EffectiveLimits(BaseModel):
    """Merged limits from all user roles (most permissive wins)."""

    agent_calls_limit: Annotated[int | None, Field(description="Max agent calls per period. None = unlimited")] = None
    agent_calls_period: Annotated[str, Field(description="Period for limit reset (1mo, 1d, 1h)")] = "1mo"


class AgentUsage(BaseModel):
    """Current agent usage stats for a user."""

    current_count: Annotated[int, Field(description="Number of agent calls in current period")]
    limit: Annotated[int | None, Field(description="Max allowed calls. None = unlimited")]
    period: Annotated[str, Field(description="Period duration (1mo, 1d, 1h)")]
    reset_at: Annotated[datetime | None, Field(description="When the counter resets")]
    is_over_limit: Annotated[bool, Field(description="True if limit exceeded")]
    usage_percent: Annotated[float | None, Field(description="Usage as percentage (0-100). None if unlimited")]


LIMIT_EXCEEDED_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "title": "Agent Limit Reached",
        "message": "You've reached your agent call limit for this period.",
        "details": "Current usage: {current}/{limit} calls ({usage_percent:.0f}%)",
        "reset": "Your limit will reset on {reset_date}.",
        "contact": "Please contact your administrator if you need additional capacity.",
    },
    "de": {
        "title": "Agent-Limit erreicht",
        "message": "Sie haben Ihr Agent-Aufruf-Limit für diesen Zeitraum erreicht.",
        "details": "Aktuelle Nutzung: {current}/{limit} Aufrufe ({usage_percent:.0f}%)",
        "reset": "Ihr Limit wird am {reset_date} zurückgesetzt.",
        "contact": "Bitte kontaktieren Sie Ihren Administrator, wenn Sie zusätzliche Kapazität benötigen.",
    },
    "fr": {
        "title": "Limite d'agent atteinte",
        "message": "Vous avez atteint votre limite d'appels d'agent pour cette période.",
        "details": "Utilisation actuelle: {current}/{limit} appels ({usage_percent:.0f}%)",
        "reset": "Votre limite sera réinitialisée le {reset_date}.",
        "contact": "Veuillez contacter votre administrateur si vous avez besoin de capacité supplémentaire.",
    },
    "it": {
        "title": "Limite agente raggiunto",
        "message": "Hai raggiunto il limite di chiamate agente per questo periodo.",
        "details": "Utilizzo attuale: {current}/{limit} chiamate ({usage_percent:.0f}%)",
        "reset": "Il limite verrà reimpostato il {reset_date}.",
        "contact": "Contatta il tuo amministratore se hai bisogno di capacità aggiuntiva.",
    },
}


class RoleLimitService:
    """
    Handles role-based rate limiting for agent calls.

    Uses Valkey for real-time counters and RoleEntity for limit configuration.
    When a user has multiple roles, the most permissive limit (highest value or unlimited) wins.
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    @trace_fn
    async def get_effective_limits(self, user: UserIdentity) -> EffectiveLimits:
        """
        Get merged limits for user based on their roles.
        Most permissive (highest limit or unlimited) wins.
        """
        roles = RoleEntity.get_roles_with_limits(user.roles)

        if not roles:
            return EffectiveLimits()

        limits = [r.agent_calls_limit for r in roles]

        # If any role has None (unlimited), user gets unlimited
        if None in limits:
            return EffectiveLimits(agent_calls_limit=None)

        # All roles have limits - use highest (most permissive)
        max_limit = max(limits)

        # Use period from the role with highest limit
        period = next((r.agent_calls_period for r in roles if r.agent_calls_limit == max_limit), "1mo")

        return EffectiveLimits(agent_calls_limit=max_limit, agent_calls_period=period or "1mo")

    @trace_fn
    async def check_agent_limit(self, user: UserIdentity, locale: str = "en") -> None:
        """
        Check if user is within their agent call limit.
        Raises HTTP 429 if exceeded.
        """
        limits = await self.get_effective_limits(user)

        # Unlimited - always allow
        if limits.agent_calls_limit is None:
            return

        current = await self._get_counter(user.id)

        if current >= limits.agent_calls_limit:
            reset_at = await self._get_reset_time(user.id, limits.agent_calls_period)
            raise HTTPException(
                status_code=429,
                detail=self._format_error_message(
                    current=current,
                    limit=limits.agent_calls_limit,
                    reset_at=reset_at,
                    locale=locale,
                ),
            )

    @trace_fn
    async def increment_usage(self, user_id: str, period: str = "1mo") -> int:
        """
        Increment agent call counter atomically.
        Returns new count.
        """
        key = self._counter_key(user_id)
        ttl = self._period_to_seconds(period)

        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        results = await pipe.execute()

        return int(results[0])

    @trace_fn
    async def get_agent_usage(self, user: UserIdentity) -> AgentUsage:
        """Get current usage stats for display in UI."""
        limits = await self.get_effective_limits(user)
        current = await self._get_counter(user.id)
        reset_at = await self._get_reset_time(user.id, limits.agent_calls_period)

        # Calculate usage percentage
        usage_percent = None
        if limits.agent_calls_limit is not None and limits.agent_calls_limit > 0:
            usage_percent = (current / limits.agent_calls_limit) * 100

        return AgentUsage(
            current_count=current,
            limit=limits.agent_calls_limit,
            period=limits.agent_calls_period,
            reset_at=reset_at,
            is_over_limit=(limits.agent_calls_limit is not None and current >= limits.agent_calls_limit),
            usage_percent=usage_percent,
        )

    def _counter_key(self, user_id: str) -> str:
        """Build Valkey key for user's agent call counter."""
        return f"ratelimit:agent:{user_id}"

    async def _get_counter(self, user_id: str) -> int:
        """Get current counter value from Valkey."""
        value = await self.redis.get(self._counter_key(user_id))
        return int(value) if value else 0

    async def _get_reset_time(self, user_id: str, period: str) -> datetime | None:
        """Get when the counter will reset based on TTL."""
        ttl = await self.redis.ttl(self._counter_key(user_id))
        if ttl > 0:
            return datetime.now(UTC) + timedelta(seconds=ttl)
        # No existing counter - would reset after period from now
        return datetime.now(UTC) + timedelta(seconds=self._period_to_seconds(period))

    def _period_to_seconds(self, period: str) -> int:
        """Convert period string (1mo, 1d, 1h) to seconds."""
        match = re.match(r"(\d+)(mo|d|h|m|s)", period)
        if not match:
            return 2592000  # Default 30 days

        value, unit = int(match.group(1)), match.group(2)
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "mo": 2592000}
        return value * multipliers.get(unit, 2592000)

    def _format_error_message(
        self,
        current: int,
        limit: int,
        reset_at: datetime | None,
        locale: str,
    ) -> str:
        """Format user-friendly error message with localization."""
        messages = LIMIT_EXCEEDED_MESSAGES.get(locale, LIMIT_EXCEEDED_MESSAGES["en"])

        reset_date = reset_at.strftime("%d.%m.%Y") if reset_at else "soon"
        usage_percent = (current / limit) * 100 if limit > 0 else 0

        parts = [
            f"**{messages['title']}**",
            "",
            messages["message"],
            "",
            messages["details"].format(current=current, limit=limit, usage_percent=usage_percent),
            messages["reset"].format(reset_date=reset_date),
            "",
            messages["contact"],
        ]

        return "\n".join(parts)
