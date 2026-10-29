import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Awaitable, Callable

logger = logging.getLogger(__name__)

# Long enough that a short document never sends one, short enough that a chat never looks stalled.
HEARTBEAT_SECONDS = 60.0


class ReadingHeartbeat:
    """Says, at intervals, that a document is still being read.

    One answer extracts every document of a selection, and a long document can take minutes; without a sign of life
    the user cannot tell a slow extraction from one that hangs. The heartbeat stops with the reading it accompanies.
    """

    @staticmethod
    @contextlib.asynccontextmanager
    async def around(
        say: Callable[[int], Awaitable[None]], interval_seconds: float = HEARTBEAT_SECONDS
    ) -> AsyncIterator[None]:
        """Calls `say` with the minutes elapsed every `interval_seconds` while the body runs."""
        task = asyncio.create_task(ReadingHeartbeat._beat(say, interval_seconds))
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    @staticmethod
    async def _beat(say: Callable[[int], Awaitable[None]], interval_seconds: float) -> None:
        """A sign of life that cannot be shown is skipped: it must never fail the reading it accompanies."""
        beats = 0
        while True:
            await asyncio.sleep(interval_seconds)
            beats += 1
            try:
                await say(max(1, round(beats * interval_seconds / 60)))
            except Exception:
                logger.warning("[record-extraction] could not show that a document is still read", exc_info=True)
