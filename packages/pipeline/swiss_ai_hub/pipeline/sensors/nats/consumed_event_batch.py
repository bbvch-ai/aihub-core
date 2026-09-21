import logging
from collections.abc import Callable
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.events.pipeline import SourceUpdatedEvent
from swiss_ai_hub.core.polling import JSPoller, PolledMessage

logger = logging.getLogger(__name__)

_FETCH_SIZE = 100
_FETCH_TIMEOUT_SECONDS = 1.0

# Messages are held unacknowledged until the tick decides, so the drain must finish well inside the
# consumer's ack deadline (30 s by JetStream default, which JSPoller does not override) and inside
# the 60 s deadline the Dagster daemon puts on a sensor evaluation. Stopping on a short fetch is
# what bounds the loop; max_ack_pending (1000 by default) caps how much one drain can hold, so this
# is only a backstop for a deployment that raises it.
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
        """Fetches until a fetch comes back short of the batch size, rather than taking a single one.

        One fetch per tick caps intake at the batch size per minute, which is what stretches a bulk
        upload into one sensor tick per ten files. A short fetch means the stream had nothing more
        immediately available, so it is the signal that this tick has caught up. Waiting for a fetch
        to come back completely empty is not: while an upload is still running the stream is never
        empty, and the loop would follow the producer until the tick blew its deadline. Leftovers are
        harmless — single-flight bounds the run count, and an observation scans the whole bucket
        regardless of which events triggered it.
        """
        messages: list[PolledMessage] = []

        while True:
            fetched = 0
            async for polled_message in poller.poll(batch_size=_FETCH_SIZE, timeout=_FETCH_TIMEOUT_SECONDS):
                fetched += 1
                if isinstance(polled_message.event, SourceUpdatedEvent):
                    messages.append(polled_message)
                    continue
                logger.warning(f"Unexpected event type: {type(polled_message.event)}")
                await polled_message.nak()

            if fetched < _FETCH_SIZE:
                return cls(messages=messages)

            if len(messages) >= _MAX_DRAIN_MESSAGES:
                logger.info(f"Stopping drain at {len(messages)} events; the rest is collected next tick.")
                return cls(messages=messages)

    @classmethod
    async def drain_grouped(
        cls,
        poller: Annotated[JSPoller, "Poller for this pipeline type's single event stream"],
        bucket_of: Annotated[Callable[[str], str], "Resolves a message subject to the bucket it concerns"],
    ) -> dict[str, Self]:
        """Drains the one type-keyed stream and splits the batch per knowledge database.

        One stream carries the uploads of every database this pipeline owns, but each database gets its
        own debounce state and its own observation run, so the batch has to be grouped before it is
        folded into any cursor.
        """
        batch = await cls.drain(poller)

        grouped: dict[str, list[PolledMessage]] = {}
        for message in batch.messages:
            grouped.setdefault(bucket_of(message.subject), []).append(message)
        return {bucket: cls(messages=messages) for bucket, messages in grouped.items()}

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
