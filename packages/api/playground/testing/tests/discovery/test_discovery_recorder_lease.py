"""Exactly one API process records discovery rounds, and it keeps doing so across rounds until it stops."""

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import Redis
from swiss_ai_hub.core.discovery import DiscoveryKind, DiscoverySettings
from swiss_ai_hub.core.infrastructure import RedisSettings

from swiss_ai_hub.api.services.discovery_recorder_lease import DiscoveryRecorderLease


@pytest_asyncio.fixture
async def redis() -> AsyncIterator[Redis]:
    """Function-scoped: pytest-asyncio gives each test a fresh event loop, and a pooled client binds to the first."""
    client = RedisSettings.create_client()
    try:
        await client.ping()
    except Exception as unreachable:
        await client.aclose()
        if os.getenv("CI"):
            pytest.fail(f"Redis must be reachable in CI; the single-recorder proof cannot be skipped ({unreachable})")
        pytest.skip(f"Redis is not reachable; start the dev stack ({unreachable})")
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def key_prefix(redis: Redis) -> AsyncIterator[str]:
    prefix = f"itest:discovery:{uuid4().hex[:8]}"
    yield prefix
    keys = [key async for key in redis.scan_iter(match=f"{prefix}:*")]
    if keys:
        await redis.delete(*keys)


def _lease(redis: Redis, key_prefix: str, kind: DiscoveryKind = DiscoveryKind.AGENT) -> DiscoveryRecorderLease:
    return DiscoveryRecorderLease(redis, kind, DiscoverySettings(), key_prefix=key_prefix)


@pytest.mark.asyncio
async def test_only_one_of_several_processes_holds_it_round_after_round(redis: Redis, key_prefix: str) -> None:
    first, second, third = (_lease(redis, key_prefix) for _ in range(3))

    for _ in range(3):
        assert [await first.held(), await second.held(), await third.held()] == [True, False, False]


@pytest.mark.asyncio
async def test_stopping_hands_it_to_the_next_process(redis: Redis, key_prefix: str) -> None:
    first, second = _lease(redis, key_prefix), _lease(redis, key_prefix)
    assert await first.held()

    await first.release()

    assert await second.held()
    assert not await first.held()


@pytest.mark.asyncio
async def test_a_lease_that_expired_is_taken_over(redis: Redis, key_prefix: str) -> None:
    """The holder died without releasing; the TTL is what lets another process take over."""
    first, second = _lease(redis, key_prefix), _lease(redis, key_prefix)
    assert await first.held()

    await redis.delete(f"{key_prefix}:{DiscoveryKind.AGENT}:recorder")

    assert await second.held()
    assert not await first.held()


@pytest.mark.asyncio
async def test_agent_and_process_rounds_have_separate_leases(redis: Redis, key_prefix: str) -> None:
    assert await _lease(redis, key_prefix, DiscoveryKind.AGENT).held()
    assert await _lease(redis, key_prefix, DiscoveryKind.PROCESS).held()


@pytest.mark.asyncio
async def test_releasing_a_lease_never_held_is_harmless(redis: Redis, key_prefix: str) -> None:
    await _lease(redis, key_prefix).release()
