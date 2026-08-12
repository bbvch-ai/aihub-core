import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from redis.asyncio import Redis
from redis.exceptions import LockError

logger = logging.getLogger(__name__)

_LEADER_KEY = "scheduler:leader"
_WATERMARK_KEY = "scheduler:watermark"
_CLAIM_KEY_PREFIX = "scheduler:fired"


class ScheduleStateStore:
    """All scheduler state, held exclusively in Redis.

    Keeping every piece of state here — leadership, the tick watermark, and the per-occurrence claims —
    is what lets the scheduler move from the API into `aihub-daemon` without touching agent- or
    runner-side code: the new host reads the same keys and resumes where the old one stopped.

    Two distinct mechanisms guard against duplicate runs, and both are needed. The leader lease stops
    two API replicas from ticking at the same time. The per-occurrence claim stops the *same* occurrence
    firing twice when a leader dies mid-tick and another replica takes over before the watermark advanced.
    """

    def __init__(self, *, redis: Redis, lease_ttl: int, claim_ttl: int) -> None:
        self._redis = redis
        self._lease_ttl = lease_ttl
        self._claim_ttl = claim_ttl

    @asynccontextmanager
    async def leadership(self) -> AsyncIterator[bool]:
        """Acquires the singleton scheduler lease, yielding whether this replica is the leader.

        Non-blocking: a replica that loses the race skips the tick rather than queueing, because the
        holder is already covering the same window. `lease_ttl` must exceed the worst-case tick runtime,
        or the lease expires mid-tick and a second replica can start one concurrently.
        """
        lock = self._redis.lock(_LEADER_KEY, timeout=self._lease_ttl)
        if not await lock.acquire(blocking=False):
            logger.debug("Scheduler tick skipped: another replica holds the leader lease")
            yield False
            return
        try:
            yield True
        finally:
            try:
                await lock.release()
            except LockError:
                logger.warning("Scheduler leader lease expired before release; consider raising SCHEDULER_LEASE_TTL")

    async def claim_occurrence(self, agent_class: str, agent_id: str, occurrence: datetime) -> bool:
        """Claims one occurrence for firing, returning False if it was already claimed.

        `SET NX` makes the claim atomic, so exactly one replica ever gets True for a given
        (agent, occurrence) pair. The claim outlives the catch-up window so a replay after downtime
        cannot re-fire an occurrence that already ran.
        """
        key = f"{_CLAIM_KEY_PREFIX}:{agent_class}:{agent_id}:{occurrence.isoformat()}"
        return bool(await self._redis.set(key, "1", nx=True, ex=self._claim_ttl))

    async def get_watermark(self) -> datetime | None:
        """The end of the last completed tick window, or None on a cold start."""
        stored = await self._redis.get(_WATERMARK_KEY)
        if stored is None:
            return None
        raw = stored.decode() if isinstance(stored, bytes) else stored
        return datetime.fromisoformat(raw).astimezone(UTC)

    async def set_watermark(self, watermark: datetime) -> None:
        await self._redis.set(_WATERMARK_KEY, watermark.astimezone(UTC).isoformat())
