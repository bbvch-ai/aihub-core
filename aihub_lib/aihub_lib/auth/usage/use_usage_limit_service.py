from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from redis.asyncio import Redis

from aihub_lib.auth.usage.RateLimitStore import RateLimitStore
from aihub_lib.infrastructure.redis.use_redis import use_redis

if TYPE_CHECKING:
    from aihub_lib.auth.usage.UsageLimitService import UsageLimitService


def use_rate_limit_store(redis: Annotated[Redis, Depends(use_redis)]) -> RateLimitStore:
    """FastAPI dependency that provides a RateLimitStore instance."""
    return RateLimitStore(redis)


def use_usage_limit_service(
    store: Annotated[RateLimitStore, Depends(use_rate_limit_store)],
) -> UsageLimitService:
    """FastAPI dependency that provides a UsageLimitService instance."""
    from aihub_lib.auth.usage.UsageLimitService import UsageLimitService

    return UsageLimitService(store)
