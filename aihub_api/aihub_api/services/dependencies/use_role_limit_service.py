from functools import lru_cache

from aihub_lib.auth.access.RoleLimitService import RoleLimitService
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from redis.asyncio import Redis


@lru_cache
def _get_redis_client() -> Redis:
    """Cached Redis client instance."""
    return RedisSettings.create_client()


def use_role_limit_service() -> RoleLimitService:
    """FastAPI dependency that provides a RoleLimitService instance."""
    return RoleLimitService(redis=_get_redis_client())
