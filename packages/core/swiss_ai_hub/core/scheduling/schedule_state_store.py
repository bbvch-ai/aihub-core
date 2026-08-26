import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from redis.asyncio import Redis
from redis.exceptions import LockError

logger = logging.getLogger(__name__)

DEFAULT_KEY_PREFIX = "scheduler"

_LEADER_SUFFIX = "leader"
_WATERMARK_SUFFIX = "watermark"
_CLAIM_SUFFIX = "fired"
_RETENTION_SUFFIX = "retention"


class ScheduleStateStore:
    """All scheduler state, held exclusively in Redis.

    Keeping every piece of state here — leadership, the tick watermark, and the per-occurrence claims —
    is what lets the scheduler move from the API into `aihub-daemon` without touching agent- or
    runner-side code: the new host reads the same keys and resumes where the old one stopped.

    Two distinct mechanisms guard against duplicate runs, and both are needed. The leader lease stops
    two API replicas from ticking at the same time. The per-occurrence claim stops the *same* occurrence
    firing twice when a leader dies mid-tick and another replica takes over before the watermark advanced.
    """

    def __init__(
        self,
        *,
        redis: Redis,
        lease_ttl: int,
        claim_ttl: int,
        key_prefix: str = DEFAULT_KEY_PREFIX,
    ) -> None:
        self._redis = redis
        self._lease_ttl = lease_ttl
        self._claim_ttl = claim_ttl
        # Every key hangs off one prefix so a second scheduler can coordinate independently on the same
        # Redis — which is what makes a two-replica test isolable from a developer's running API, since
        # `RedisSettings` exposes only a URL and offers no database to switch to.
        self._key_prefix = key_prefix

    def _key(self, suffix: str) -> str:
        return f"{self._key_prefix}:{suffix}"

    @asynccontextmanager
    async def leadership(self) -> AsyncIterator[bool]:
        """Acquires the singleton scheduler lease, yielding whether this replica is the leader.

        Non-blocking: a replica that loses the race skips the tick rather than queueing, because the
        holder is already covering the same window. `lease_ttl` must exceed the worst-case tick runtime,
        or the lease expires mid-tick and a second replica can start one concurrently.
        """
        lock = self._redis.lock(self._key(_LEADER_SUFFIX), timeout=self._lease_ttl)
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
                logger.warning(
                    "Scheduler leader lease expired mid-tick; another replica may already hold it. "
                    "Raise the lease_ttl passed to CronScheduler if ticks routinely outrun %ss",
                    self._lease_ttl,
                )

    async def claim_occurrence(self, agent_class: str, agent_id: str, occurrence: datetime) -> bool:
        """Claims one occurrence for firing, returning False if it was already claimed.

        `SET NX` makes the claim atomic, so exactly one replica ever gets True for a given
        (agent, occurrence) pair. The claim outlives the catch-up window so a replay after downtime
        cannot re-fire an occurrence that already ran.
        """
        key = self._key(f"{_CLAIM_SUFFIX}:{agent_class}:{agent_id}:{occurrence.isoformat()}")
        return bool(await self._redis.set(key, "1", nx=True, ex=self._claim_ttl))

    async def get_watermark(self) -> datetime | None:
        """The end of the last completed tick window, or None on a cold start."""
        stored = await self._redis.get(self._key(_WATERMARK_SUFFIX))
        if stored is None:
            return None
        raw = stored.decode() if isinstance(stored, bytes) else stored
        return datetime.fromisoformat(raw).astimezone(UTC)

    async def set_watermark(self, watermark: datetime) -> None:
        await self._redis.set(self._key(_WATERMARK_SUFFIX), watermark.astimezone(UTC).isoformat())

    async def claim_retention_window(self, ttl_seconds: int) -> bool:
        """Claims the right to prune for the next `ttl_seconds`, returning False if it is already claimed.

        Pruning is bulk deletion, so it belongs nowhere near the per-tick hot path. The same `SET NX EX`
        shape as an occurrence claim gives that for one Redis round-trip per tick: whichever leader wins
        prunes, and every tick until the key expires skips it — cluster-wide, without a second timer.
        """
        key = self._key(_RETENTION_SUFFIX)
        return bool(await self._redis.set(key, "1", nx=True, ex=ttl_seconds))
