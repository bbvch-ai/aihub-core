import logging
from datetime import timedelta

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "mailbox:run_lease"

# Covers one message's work plus generous slack, not a whole batch — the lease is renewed per message, so this
# bounds how long a *crashed* run blocks its successor, never how long a healthy run may take. The shipped
# classification template caps a single LLM call at timeout=60.0.
LEASE_TTL = timedelta(minutes=10)


class MailboxRunLease:
    """Lets one run at a time hold a profile's mailbox.

    Filing is the classification agent's only dedup: a message is safe from reprocessing once it has left the inbox,
    and stays unread right up until then. A second run starting inside that window re-lists the same UIDs, re-archives
    them to the data lake, re-classifies them at full LLM cost, and then either double-files on the COPY + UID EXPUNGE
    path or fails on a vanished UID. Two cron occurrences overlapping on a slow mailbox is exactly that window, and the
    scheduler's per-occurrence claim does not help — those are two *distinct* occurrences.

    `SET NX EX` closes it atomically, which is why this is Redis and not `ThreadContext`: `BaseContext` offers no
    set-if-absent and no per-key TTL, and its thread scope would miss a manually triggered run, since only scheduled
    runs share a thread.

    The lease is renewed per message rather than sized for a whole batch. A TTL guessed from the batch length has to be
    re-guessed every time the run grows longer, and guessing short is the dangerous direction: the lease lapses
    mid-run and the overlapping run it exists to stop starts anyway.
    """

    def __init__(self, redis: Redis, ttl: timedelta = LEASE_TTL) -> None:
        self._redis = redis
        self._ttl = int(ttl.total_seconds())

    async def acquire(self, agent_class: str, agent_id: str, run_id: str) -> bool:
        """Claim the mailbox for this run, reporting False when another run already holds it."""
        acquired = bool(await self._redis.set(self._key(agent_class, agent_id), run_id, nx=True, ex=self._ttl))
        if acquired:
            logger.info("[lease] %s/%s acquired by run %s", agent_class, agent_id, run_id)
        else:
            logger.info(
                "[lease] %s/%s already held by run %s — run %s will not start",
                agent_class,
                agent_id,
                await self._holder(agent_class, agent_id),
                run_id,
            )
        return acquired

    async def renew(self, agent_class: str, agent_id: str, run_id: str) -> None:
        """Extend this run's hold by another TTL, doing nothing when the lease is no longer ours.

        The holder is compared first: a run whose lease already expired must not extend the successor that took it,
        which a bare EXPIRE would do.
        """
        if await self._holder(agent_class, agent_id) != run_id:
            logger.warning(
                "[lease] %s/%s is no longer held by run %s — not renewing; a concurrent run may already be filing",
                agent_class,
                agent_id,
                run_id,
            )
            return

        await self._redis.expire(self._key(agent_class, agent_id), self._ttl)

    async def release(self, agent_class: str, agent_id: str, run_id: str) -> None:
        """Hand the mailbox back, doing nothing when the lease is no longer ours.

        Same reason as `renew`: a bare DEL would let a run that overran its TTL delete its successor's lease.
        """
        if await self._holder(agent_class, agent_id) != run_id:
            logger.warning("[lease] %s/%s is no longer held by run %s — not releasing", agent_class, agent_id, run_id)
            return

        await self._redis.delete(self._key(agent_class, agent_id))
        logger.info("[lease] %s/%s released by run %s", agent_class, agent_id, run_id)

    async def _holder(self, agent_class: str, agent_id: str) -> str | None:
        held = await self._redis.get(self._key(agent_class, agent_id))
        if held is None:
            return None
        return held.decode() if isinstance(held, bytes) else held

    @staticmethod
    def _key(agent_class: str, agent_id: str) -> str:
        """Deliberately outside the run_context_*/thread_context_* namespaces `BaseContext.delete_all` clears."""
        return f"{_KEY_PREFIX}:{agent_class}:{agent_id}"
