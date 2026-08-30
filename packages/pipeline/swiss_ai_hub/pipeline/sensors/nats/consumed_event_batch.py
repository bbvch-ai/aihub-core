import logging
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.events.pipeline import SourceUpdatedEvent
from swiss_ai_hub.core.polling import JSPoller, PolledMessage

logger = logging.getLogger(__name__)

_FETCH_SIZE = 100
_FETCH_TIMEOUT_SECONDS = 1.0

# Messages are held unacknowledged until the tick decides, so the drain must finish well inside the
# consumer's ack deadline (30 s by JetStream default, which JSPoller does not override). The server
# already bounds this: max_ack_pending defaults to 1000, so a fetch returns empty once that many are
# outstanding and the loop ends after ~1 s. This cap only removes the dependency on that default —
# raising max_ack_pending would otherwise let a drain run long enough for its earliest messages to
# redeliver into the same loop. A leftover backlog is harmless: single-flight bounds runs anyway and
# the next tick collects it.
_MAX_DRAIN_MESSAGES = 5_000


class ConsumedEventBatch(BaseModel):
    """The events drained from JetStream in one sensor tick, still unacknowledged.

    Acks are deferred until the sensor has decided what to do with the batch: acking first means a
    tick that fails before requesting a run drops its trigger permanently.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: list[PolledMessage] = Field(default_factory=list, description="Drained messages awaiting ack or nak")

    @classmethod
    async def drain(cls, poller: Annotated[JSPoller, "Poller for this pipeline's event stream"]) -> Self:
        """Fetches until a fetch comes back empty, rather than taking a single batch.

        One fetch per tick caps intake at the batch size per minute, which is what stretches a bulk
        upload into one sensor tick per ten files.
        """
        messages: list[PolledMessage] = []

        while True:
            fetch_had_messages = False
            async for polled_message in poller.poll(batch_size=_FETCH_SIZE, timeout=_FETCH_TIMEOUT_SECONDS):
                fetch_had_messages = True
                if isinstance(polled_message.event, SourceUpdatedEvent):
                    messages.append(polled_message)
                    continue
                logger.warning(f"Unexpected event type: {type(polled_message.event)}")
                await polled_message.nak()

            if len(messages) >= _MAX_DRAIN_MESSAGES:
                logger.info(f"Stopping drain at {len(messages)} events; the rest is collected next tick.")
                return cls(messages=messages)

            if not fetch_had_messages:
                return cls(messages=messages)

    @property
    def count(self) -> int:
        return len(self.messages)

    @property
    def max_sequence(self) -> int:
        """Highest JetStream stream sequence in the batch, used to derive a stable run key."""
        return max((message.sequence for message in self.messages), default=0)

    async def ack_all(self) -> None:
        for message in self.messages:
            await message.ack()

    async def nak_all(self) -> None:
        for message in self.messages:
            await message.nak()
