import asyncio

import pytest
from redis.exceptions import TimeoutError as RedisTimeoutError

from swiss_ai_hub.core.infrastructure.redis.redis_settings import RedisSettings

SHORT_CONNECT_TIMEOUT_SECONDS = 0.05
UPPER_BOUND_SECONDS = 60


@pytest.fixture
def redis_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.delenv("REDIS_TOKEN", raising=False)


@pytest.mark.usefixtures("redis_url")
def test_the_client_bounds_every_connect() -> None:
    client = RedisSettings.create_client()
    assert client.connection_pool.connection_kwargs["socket_connect_timeout"] == RedisSettings.CONNECT_TIMEOUT_SECONDS


@pytest.mark.usefixtures("redis_url")
def test_a_connect_that_never_completes_fails_instead_of_stalling(monkeypatch: pytest.MonkeyPatch) -> None:
    """A step awaiting Valkey used to wait for good on a connect the event loop never reported writable."""

    async def never_connects(*_args, **_kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(RedisSettings, "CONNECT_TIMEOUT_SECONDS", SHORT_CONNECT_TIMEOUT_SECONDS)
    monkeypatch.setattr(asyncio, "open_connection", never_connects)

    async def ping() -> None:
        client = RedisSettings.create_client()
        try:
            await asyncio.wait_for(client.ping(), timeout=UPPER_BOUND_SECONDS)
        finally:
            await client.aclose()

    with pytest.raises(RedisTimeoutError):
        asyncio.run(ping())
