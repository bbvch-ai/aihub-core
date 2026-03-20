import logging
from collections.abc import AsyncIterator
from typing import Annotated

from nats.js import JetStreamContext
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from nats.js.errors import NotFoundError

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.polling.polled_message import PolledMessage
from swiss_ai_hub.core.streams.stream_manager import StreamManager

logger = logging.getLogger(__name__)


class JSPoller:
    """
    Generic JetStream poller for fetching and processing events from NATS JetStream.

    Provides a reusable pattern for:
    - Ensuring streams exist
    - Creating durable consumers
    - Polling messages in batches
    - Parsing events with proper error handling
    - Managing ACK/NAK for message delivery
    """

    def __init__(
        self,
        js: Annotated[JetStreamContext, "JetStream context for stream operations"],
        stream_name: Annotated[str, "Name of the JetStream stream"],
        stream_subject: Annotated[str, "Subject pattern for the stream"],
        consumer_name: Annotated[str, "Name of the durable consumer"],
    ):
        self.js = js
        self.stream_name = stream_name
        self.stream_subject = stream_subject
        self.consumer_name = consumer_name

    async def ensure_stream_exists(self):
        """Ensure the required JetStream stream exists."""
        stream_manager = StreamManager(self.js, self.stream_name, self.stream_subject)
        await stream_manager.ensure_stream_exists()

    async def ensure_consumer_exists(
        self,
        deliver_policy: DeliverPolicy = DeliverPolicy.ALL,
        ack_policy: AckPolicy = AckPolicy.EXPLICIT,
        max_deliver: int = 3,
        filter_subject: Annotated[str | None, "Optional subject filter for the consumer"] = None,
    ):
        """Ensure the durable consumer exists with the specified configuration."""
        try:
            await self.js.consumer_info(self.stream_name, self.consumer_name)
        except NotFoundError:
            config_params = {
                "durable_name": self.consumer_name,
                "deliver_policy": deliver_policy,
                "ack_policy": ack_policy,
                "max_deliver": max_deliver,
            }
            if filter_subject:
                config_params["filter_subject"] = filter_subject

            await self.js.add_consumer(self.stream_name, config=ConsumerConfig(**config_params))

    async def poll(
        self,
        batch_size: Annotated[int, "Number of messages to fetch per batch"] = 10,
        timeout: Annotated[float, "Timeout in seconds for each fetch operation"] = 1.0,
    ) -> AsyncIterator[PolledMessage]:
        """
        Poll for new messages from the JetStream consumer.

        Yields PolledMessage objects that can be:
        - Unpacked for backwards compatibility: async for event, ack, nak in poller.poll()
        - Used directly for metadata access: async for msg in poller.poll()

        The caller is responsible for calling ack() or nak() based on processing success.
        """
        psub = await self.js.pull_subscribe(self.stream_subject, self.consumer_name)

        try:
            messages = await psub.fetch(batch=batch_size, timeout=timeout)

            for msg in messages:
                try:
                    event = BaseEvent.deserialize_event(msg.data)
                    yield PolledMessage(msg=msg, event=event)

                except Exception as e:
                    logger.exception(f"Failed to deserialize event from message: {e}")
                    await msg.nak()

        except Exception as e:
            if "timeout" not in str(e).lower():
                logger.exception(f"Error polling messages: {e}")
