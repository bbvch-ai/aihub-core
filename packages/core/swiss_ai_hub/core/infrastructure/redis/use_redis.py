from fastapi import Request
from redis.asyncio import Redis


def use_redis(request: Request) -> Redis:
    """FastAPI dependency that provides the Redis client from app state."""
    return request.app.state.redis
