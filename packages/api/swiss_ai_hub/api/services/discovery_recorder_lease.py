import logging

from redis.asyncio import Redis
from redis.exceptions import LockError
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
        """Renews the lease if this process holds it, otherwise takes it if it is free."""
        try:
            return await self._lock.reacquire()
        except LockError:
            return await self._lock.acquire(blocking=False)

    async def release(self) -> None:
        """Hands the lease over at shutdown instead of leaving the others to wait for it to expire."""
        try:
            await self._lock.release()
        except LockError:
            logger.debug("Discovery recorder lease was not held at shutdown")
