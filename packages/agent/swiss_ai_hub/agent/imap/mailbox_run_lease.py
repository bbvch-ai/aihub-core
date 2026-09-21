import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
from pathlib import Path

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "mailbox:run_lease"

_LUA_DIR = Path(__file__).parent / "lua"
_RENEW_IF_HOLDER_LUA = (_LUA_DIR / "renew_if_holder.lua").read_text()
_RELEASE_IF_HOLDER_LUA = (_LUA_DIR / "release_if_holder.lua").read_text()
_REACQUIRE_IF_FREE_OR_HOLDER_LUA = (_LUA_DIR / "reacquire_if_free_or_holder.lua").read_text()

# Bounds how long a *crashed* run blocks its successor, never how long a healthy run may take: a run holding the
# lease heartbeats it for as long as its process lives, so the TTL only starts counting down once that process is
# gone. Ten minutes is short enough that a crash costs at most a few skipped occurrences.
LEASE_TTL = timedelta(minutes=10)

# Renewing three times per TTL means two consecutive renewals have to be lost before the lease lapses under a run
# that is still alive.
_BEATS_PER_TTL = 3


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

    Renewal and release are Lua so the holder check and the write are one round trip. Reading the holder into Python
    and then acting on it leaves a window in which the lease lapses and a second run acquires it, so the first run's
    `DEL` would free a mailbox the second is actively filing — the precise failure this class exists to prevent.

    Holding is a heartbeat rather than a renewal the caller has to remember: `heartbeat()` keeps the lease alive for
    as long as its body runs, whatever that body does. Renewing at explicit points instead means every phase that
    grows past the TTL becomes a silent overlap bug, and the slow phases here — a batch fetch of up to
    `max_messages` messages, and the filing pass — have no natural per-item hook to renew from.
    """

    def __init__(self, redis: Redis, ttl: timedelta = LEASE_TTL) -> None:
        self._redis = redis
        self._ttl = int(ttl.total_seconds())
        self._lost = False

    @property
    def lost(self) -> bool:
        """Whether a heartbeat has found the lease taken from under this run.

        Checked rather than raised into the body because the body is the part that must not be interrupted
        mid-IMAP-command; the caller decides where losing the mailbox is fatal.
        """
        return self._lost

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

    async def renew(self, agent_class: str, agent_id: str, run_id: str) -> bool:
        """Extend this run's hold by another TTL, reporting False when the lease is no longer ours."""
        extended = await self._redis.eval(_RENEW_IF_HOLDER_LUA, 1, self._key(agent_class, agent_id), run_id, self._ttl)
        return bool(extended)

    async def reacquire(self, agent_class: str, agent_id: str, run_id: str) -> bool:
        """Take the mailbox back when it is still ours or has lapsed unclaimed, reporting False only when another
        run holds it.

        This reverses the class's own rule that a lost lease means stop — deliberately, and only for the phase after
        the batch has been filed.

        The rule exists because losing the lease mid-classification means a second run is working the same unread
        mail. After filing, that situation cannot arise: every message of the batch has left the inbox, so a
        concurrent run's `list_unread` finds nothing of this batch to classify, fetch or file. What remains is
        drafting, and the delegation window it spans is unbounded — a run waits on N RAG agents with no step body to
        heartbeat from, so a lapsed lease there is the expected case, not evidence of a competitor. Treating it as
        fatal would throw away a batch's drafts every time the delegates were slow, and the mail is already filed, so
        those drafts would never be retried.

        A lease another run actually holds still refuses. That run reached `acquire` after this one's lapsed, which
        means it is working *later* mail, and both runs appending into the same Drafts folder is the one thing the
        drafting phase still has to avoid.
        """
        reacquired = await self._redis.eval(
            _REACQUIRE_IF_FREE_OR_HOLDER_LUA, 1, self._key(agent_class, agent_id), run_id, self._ttl
        )
        if not reacquired:
            logger.warning(
                "[lease] %s/%s is held by run %s — run %s cannot take it back",
                agent_class,
                agent_id,
                await self._holder(agent_class, agent_id),
                run_id,
            )
            return False

        logger.info("[lease] %s/%s reacquired by run %s", agent_class, agent_id, run_id)
        return True

    async def release(self, agent_class: str, agent_id: str, run_id: str) -> None:
        """Hand the mailbox back, doing nothing when the lease is no longer ours."""
        released = await self._redis.eval(_RELEASE_IF_HOLDER_LUA, 1, self._key(agent_class, agent_id), run_id)
        if not released:
            logger.warning("[lease] %s/%s is no longer held by run %s — not releasing", agent_class, agent_id, run_id)
            return

        logger.info("[lease] %s/%s released by run %s", agent_class, agent_id, run_id)

    @asynccontextmanager
    async def heartbeat(self, agent_class: str, agent_id: str, run_id: str) -> AsyncIterator[None]:
        """Keep this run's claim alive for as long as the body runs, recording a loss in `lost`.

        This is what decouples the TTL from how long a run takes. Sizing the TTL for a whole batch means re-sizing it
        every time the run grows — #1639 adds a drafting pass over the same messages — and guessing short is the
        dangerous direction: the lease lapses mid-run and the overlap it exists to stop happens anyway.

        Losing the lease stops the heartbeat rather than reacquiring: another run holds the mailbox now, and taking it
        back would put two runs on the same messages, which is the situation being avoided.
        """
        self._lost = False
        beat = asyncio.create_task(self._beat(agent_class, agent_id, run_id))
        try:
            yield
        finally:
            beat.cancel()
            with suppress(asyncio.CancelledError):
                await beat

    async def _beat(self, agent_class: str, agent_id: str, run_id: str) -> None:
        # Floored well below any usable TTL rather than at something round like a second: a floor at or above
        # `ttl / _BEATS_PER_TTL` silently turns the heartbeat into a single renewal that races the expiry, and it
        # would do so only for short TTLs — which is exactly what tests use and production does not, so the breakage
        # would surface nowhere near the change that caused it.
        interval = max(self._ttl / _BEATS_PER_TTL, 0.1)
        while True:
            await asyncio.sleep(interval)
            if await self._renewed_or_unreachable(agent_class, agent_id, run_id):
                continue

            self._lost = True
            logger.warning(
                "[lease] %s/%s is no longer held by run %s — another run may already be filing this mailbox",
                agent_class,
                agent_id,
                run_id,
            )
            return

    async def _renewed_or_unreachable(self, agent_class: str, agent_id: str, run_id: str) -> bool:
        """A renewal that Redis refused is a lost lease; one it never answered is not.

        The distinction matters twice. A dead heartbeat task raises out of `heartbeat`'s exit, which would mask
        whatever the body was doing — a run that had already filed its mail would be reported as failed, and the
        release its terminal step owes would never happen. And a blip is not evidence the mailbox changed hands: no
        second run can acquire while Redis is unreachable either, so retrying on the next beat is both safe and much
        cheaper than abandoning a batch that has already paid for its model calls.

        Only a definitive "not yours" is treated as a loss.
        """
        try:
            return await self.renew(agent_class, agent_id, run_id)
        except Exception:
            logger.warning(
                "[lease] could not reach Redis to renew %s/%s for run %s — retrying on the next beat",
                agent_class,
                agent_id,
                run_id,
                exc_info=True,
            )
            return True

    async def _holder(self, agent_class: str, agent_id: str) -> str | None:
        held = await self._redis.get(self._key(agent_class, agent_id))
        if held is None:
            return None
        return held.decode() if isinstance(held, bytes) else held

    @staticmethod
    def _key(agent_class: str, agent_id: str) -> str:
        """Deliberately outside the run_context_*/thread_context_* namespaces `BaseContext.delete_all` clears."""
        return f"{_KEY_PREFIX}:{agent_class}:{agent_id}"
