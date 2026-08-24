"""Exercised against the real Valkey the rest of the agent suite already needs.

A fake would be testing the fake: the whole point of this class is that `SET NX EX` is atomic and that TTLs
actually expire, and neither property survives being reimplemented in a stub.
"""

import asyncio
from datetime import timedelta
from uuid import uuid4

from swiss_ai_hub.core.infrastructure import RedisSettings
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.mailbox_run_lease import MailboxRunLease

_AGENT_CLASS = "EmailClassificationAgent"


def _agent_id() -> str:
    """A fresh profile per test, so tests never contend for the same key."""
    return f"mailbox-{uuid4().hex}"


def _lease(ttl: timedelta = timedelta(minutes=10)) -> tuple[MailboxRunLease, object]:
    redis = RedisSettings.create_client()
    return MailboxRunLease(redis, ttl=ttl), redis


@async_test
async def test_only_one_run_can_hold_a_mailbox():
    lease, redis = _lease()
    agent_id = _agent_id()
    try:
        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-a") is True
        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-a")
        await redis.aclose()


@async_test
async def test_releasing_lets_the_next_run_in():
    lease, redis = _lease()
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")
        await lease.release(_AGENT_CLASS, agent_id, "run-a")

        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is True
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()


@async_test
async def test_a_foreign_run_cannot_release_the_holders_lease():
    """A run that overran its TTL must not delete the lease its successor now holds."""
    lease, redis = _lease()
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")

        await lease.release(_AGENT_CLASS, agent_id, "run-stale")

        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-a")
        await redis.aclose()


@async_test
async def test_renewing_keeps_a_long_run_holding_the_mailbox():
    """The lease outlives its own TTL as long as the run keeps renewing — this is what decouples the TTL from
    however long a batch takes."""
    lease, redis = _lease(ttl=timedelta(seconds=2))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")

        for _ in range(3):
            await asyncio.sleep(1)
            await lease.renew(_AGENT_CLASS, agent_id, "run-a")

        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-a")
        await redis.aclose()


@async_test
async def test_a_foreign_run_cannot_renew_the_holders_lease():
    lease, redis = _lease(ttl=timedelta(seconds=2))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")

        await lease.renew(_AGENT_CLASS, agent_id, "run-stale")
        await asyncio.sleep(2.5)

        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is True
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()


@async_test
async def test_a_crashed_run_stops_blocking_once_the_lease_expires():
    """The only recovery path for a run that raised: the dispatcher tears down on ExceptionEvent before any step
    could release, so nothing but the TTL frees the mailbox."""
    lease, redis = _lease(ttl=timedelta(seconds=1))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-that-crashed")

        await asyncio.sleep(1.5)

        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is True
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()
