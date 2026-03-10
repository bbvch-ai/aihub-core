from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from redis.asyncio import Redis

from swiss_ai_hub.core.infrastructure.redis.use_redis import use_redis

if TYPE_CHECKING:
    from swiss_ai_hub.core.auth.usage.UsageLimits import UsageLimits


def use_usage_limits(
    redis: Annotated[Redis, Depends(use_redis)],
) -> UsageLimits:
    """FastAPI dependency that provides a UsageLimits instance."""
    from swiss_ai_hub.core.auth.usage.UsageLimits import UsageLimits

    return UsageLimits(redis)
