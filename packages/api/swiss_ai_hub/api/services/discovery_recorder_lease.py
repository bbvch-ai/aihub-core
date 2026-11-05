import logging

from redis.asyncio import Redis
from redis.exceptions import LockError, RedisError
from swiss_ai_hub.core.discovery import DiscoveryKind, DiscoverySettings

logger = logging.getLogger(__name__)


class DiscoveryRecorderLease:
    """Lets exactly one API process record discovery rounds of a kind.

    Every process still runs its own rounds, since each registers the dynamic endpoints on its own app.
    Only the rounds counted towards offline status must come from one process, or N processes would make
    "the last N rounds" span a fraction of the configured time. The lease is held across rounds, not per
    round, because the processes' rounds run seconds apart and a per-round lock would let each record.
    """

    def __init__(self, redis: Redis, kind: DiscoveryKind, settings: DiscoverySettings, key_prefix: str = "discovery"):
        # The prefix lets a test hold its own lease next to a developer's running API, which holds the real one
        self._lock = redis.lock(f"{key_prefix}:{kind}:recorder", timeout=settings.recorder_lease_ttl)

    async def held(self) -> bool:
        """Whether this process may record the round; False while Redis is unreachable.

        Redis must not decide whether a round runs at all: the round also reconciles this process's
        endpoints, and that only needs NATS and the database. Unrecorded rounds are safe, since online
        status then falls back to `MAX_SILENCE_SECONDS`.
        """
        try:
            return await self._renew_or_take()
        except RedisError as e:
            logger.warning(f"Discovery recorder lease unavailable, this round is not recorded: {e}")
            return False

    async def _renew_or_take(self) -> bool:
        try:
            return await self._lock.reacquire()
        except LockError:
            return await self._lock.acquire(blocking=False)

    async def release(self) -> None:
        """Hands the lease over at shutdown instead of leaving the others to wait for it to expire."""
        try:
            await self._lock.release()
        except RedisError as e:
            logger.debug(f"Discovery recorder lease not released at shutdown, it expires on its own: {e}")
