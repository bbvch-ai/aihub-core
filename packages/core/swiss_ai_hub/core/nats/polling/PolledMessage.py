from typing import Annotated

from nats.aio.msg import Msg

from swiss_ai_hub.core.nats.events import BaseEvent


class PolledMessage:
    """
    Wrapper for a polled NATS JetStream message with metadata and acknowledgment functions.

    Supports backwards-compatible unpacking:
        async for event, ack, nak in poller.poll():
            ...

    Or direct attribute access for metadata:
        async for msg in poller.poll():
            subject = msg.subject
            sequence = msg.sequence
            await msg.ack()
    """

    def __init__(
        self,
        msg: Annotated[Msg, "NATS JetStream message"],
        event: Annotated[BaseEvent, "Deserialized event"],
    ):
        self.event = event
        self.subject = msg.subject
        self.sequence = msg.metadata.sequence.stream
        self._msg = msg

    async def ack(self):
        """Acknowledge the message as successfully processed."""
        await self._msg.ack()

    async def nak(self):
        """Negatively acknowledge the message for redelivery."""
        await self._msg.nak()

    def __iter__(self):
        """Support unpacking: event, ack, nak = polled_message"""

        async def ack():
            await self._msg.ack()

        async def nak():
            await self._msg.nak()

        return iter((self.event, ack, nak))
