"""Exercised against the real Valkey the rest of the agent suite already needs.

A fake would be testing the fake: the whole point of this class is that `SET NX EX` is atomic, that the compare and
the write in `renew`/`release` happen in one round trip, and that TTLs actually expire. None of those properties
survive being reimplemented in a stub.
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
async def test_a_lapsed_run_does_not_release_the_lease_its_successor_took():
    """The interleaving a read-compare-write release cannot survive, and the reason `release` is Lua.

    Run A's lease is allowed to expire and run B takes the mailbox before A gets around to releasing. A read of the
    holder followed by a `DEL` in Python would free a mailbox B is actively filing, letting a third run in on the
    same messages — the exact double-filing the lease exists to prevent.
    """
    lease, redis = _lease(ttl=timedelta(seconds=1))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")
        await asyncio.sleep(1.5)
        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is True

        await lease.release(_AGENT_CLASS, agent_id, "run-a")

        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-c") is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()


@async_test
async def test_a_lapsed_run_does_not_extend_the_lease_its_successor_took():
    """The same interleaving for `renew`: run A must not push out the expiry of a lease it no longer owns."""
    lease, redis = _lease(ttl=timedelta(seconds=1))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")
        await asyncio.sleep(1.5)
        await lease.acquire(_AGENT_CLASS, agent_id, "run-b")

        assert await lease.renew(_AGENT_CLASS, agent_id, "run-a") is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
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
            assert await lease.renew(_AGENT_CLASS, agent_id, "run-a") is True

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

        assert await lease.renew(_AGENT_CLASS, agent_id, "run-stale") is False
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


@async_test
async def test_a_heartbeat_holds_the_mailbox_across_work_longer_than_the_ttl():
    """What makes the TTL a crash bound rather than a guess at how long a batch takes: the body here outlives the
    TTL several times over without the caller renewing anything."""
    lease, redis = _lease(ttl=timedelta(seconds=1))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")

        async with lease.heartbeat(_AGENT_CLASS, agent_id, "run-a"):
            await asyncio.sleep(3)
            assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is False

        assert lease.lost is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-a")
        await redis.aclose()


@async_test
async def test_a_heartbeat_reports_a_mailbox_taken_from_under_a_running_run():
    """`lost` is what the agent checks before filing. Without it a run whose lease lapsed files anyway, which is the
    double-filing the whole class exists to prevent."""
    lease, redis = _lease(ttl=timedelta(seconds=1))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")

        async with lease.heartbeat(_AGENT_CLASS, agent_id, "run-a"):
            await redis.set(MailboxRunLease._key(_AGENT_CLASS, agent_id), "run-b", ex=30)
            await asyncio.sleep(1.5)

        assert lease.lost is True
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()


@async_test
async def test_a_heartbeat_stops_when_its_body_finishes():
    """A beat that outlived its body would keep a mailbox claimed for a run that is no longer working on it."""
    lease, redis = _lease(ttl=timedelta(seconds=1))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")
        async with lease.heartbeat(_AGENT_CLASS, agent_id, "run-a"):
            await asyncio.sleep(0.1)

        await asyncio.sleep(1.5)

        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is True
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()


@async_test
async def test_a_heartbeat_survives_a_redis_blip_without_abandoning_the_run():
    """A renewal Redis never answered is not evidence the mailbox changed hands.

    The failure this pins is subtler than a wrong verdict: an unhandled error in the beat task surfaces out of the
    context manager's exit, so a run that had already filed its mail would be reported as failed and would never
    release its lease.
    """
    lease, redis = _lease(ttl=timedelta(seconds=2))
    agent_id = _agent_id()
    blips = 0

    async def flaky(*args, **kwargs):
        nonlocal blips
        blips += 1
        if blips == 1:
            raise ConnectionError("valkey went away")
        return await MailboxRunLease.renew(lease, *args, **kwargs)

    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")
        lease.renew = flaky

        async with lease.heartbeat(_AGENT_CLASS, agent_id, "run-a"):
            await asyncio.sleep(2)

        assert blips > 1, "the beat stopped at the first error instead of retrying"
        assert lease.lost is False
        assert await lease.acquire(_AGENT_CLASS, agent_id, "run-b") is False
    finally:
        del lease.renew
        await lease.release(_AGENT_CLASS, agent_id, "run-a")
        await redis.aclose()


@async_test
async def test_a_run_takes_back_a_lease_that_lapsed_unclaimed():
    """The delegation window has nothing to heartbeat from, so a lapsed lease there is expected, not a competitor.

    By that point every message of the batch has been filed out of the inbox, so no concurrent run can be working
    the same mail — and refusing would throw away a whole batch's drafts that nothing will ever retry.
    """
    lease, redis = _lease(ttl=timedelta(seconds=1))
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")
        await asyncio.sleep(1.5)

        assert await lease.renew(_AGENT_CLASS, agent_id, "run-a") is False, "precondition: the lease has lapsed"
        assert await lease.reacquire(_AGENT_CLASS, agent_id, "run-a") is True
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-a")
        await redis.aclose()


@async_test
async def test_a_run_that_still_holds_its_lease_simply_extends_it():
    lease, redis = _lease()
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-a")

        assert await lease.reacquire(_AGENT_CLASS, agent_id, "run-a") is True
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-a")
        await redis.aclose()


@async_test
async def test_a_mailbox_another_run_holds_is_never_taken_back():
    """The one case reacquire must still refuse: two runs appending into the same Drafts folder."""
    lease, redis = _lease()
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-b")

        assert await lease.reacquire(_AGENT_CLASS, agent_id, "run-a") is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()


@async_test
async def test_taking_a_lease_back_does_not_hand_it_to_the_taker_when_someone_else_holds_it():
    """A refused reacquire must leave the real holder in place, not overwrite it."""
    lease, redis = _lease()
    agent_id = _agent_id()
    try:
        await lease.acquire(_AGENT_CLASS, agent_id, "run-b")
        await lease.reacquire(_AGENT_CLASS, agent_id, "run-a")

        assert await lease.renew(_AGENT_CLASS, agent_id, "run-b") is True
        assert await lease.renew(_AGENT_CLASS, agent_id, "run-a") is False
    finally:
        await lease.release(_AGENT_CLASS, agent_id, "run-b")
        await redis.aclose()
