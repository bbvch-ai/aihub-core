from fastapi import Request
from redis.asyncio import Redis


def use_redis(request: Request) -> Redis:
    return request.app.state.redis