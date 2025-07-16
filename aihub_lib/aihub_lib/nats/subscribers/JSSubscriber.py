import asyncio
import logging
from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS
from nats.errors import MsgAlreadyAckdError
from nats.js import JetStreamContext

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.nats.streams.StreamManager import StreamManager
from aihub_lib.nats.subscribers.AbstractSubscriber import AbstractSubscriber, TEvent
from aihub_lib.nats.topics import Topic

logger = logging.getLogger(__name__)


class JSSubscriber(AbstractSubscriber):
    """
    A subscriber that leverages NATS JetStream for consuming events from persistent streams.
    It ensures the stream is present (creating it if necessary), subscribes to a specified subject,
    deserializes events, and invokes a handler function.

    ### Why JSSubscriber?
    While a basic subscriber might handle ephemeral subjects, JSSubscriber integrates with JetStream to:
    - Guarantee message durability and replay via persistent streams.
    - Integrate into queue groups for load balancing consumers.
    - Provide automatic ack-on-fail behavior, ensuring that messages aren't lost on exceptions.

    ### Key Features
    - **Stream Management:** Automatically ensures that the corresponding stream is created and configured.
    - **Event Deserialization:** Converts raw message data into typed event instances.
    - **Topic Parsing:** Transforms the NATS subject into a structured `Topic` for context-aware handling.
    - **Queue Groups:** Allows multiple subscribers to share a single queue, distributing load.
    """

    # Class-level semaphore to limit concurrent processing
    _process_semaphore = asyncio.Semaphore(1000)

    def __init__(
        self,
        nc: NATS,
        subject: str,
        stream_name: str,
        stream_subject: str,
        queue_group: str,
        event_cls: type[TEvent],
        handler: Callable[[TEvent, Topic], Awaitable[None]],
        js: JetStreamContext | None = None,
        agent_config_type: type[AgentConfig] = AgentConfig,
    ):
        super().__init__(nc, subject, event_cls, handler)
        self.js = js or nc.jetstream()
        self.queue_group = queue_group
        self.stream_manager = StreamManager(self.js, stream_name, stream_subject)
        self.js_subscription: JetStreamContext.PushSubscription | None = None
        self.agent_config_type = agent_config_type

    async def start(self):
        """
        Ensures the stream exists and subscribes to the subject with the given queue group.
        Once started, the subscriber begins consuming messages from JetStream.
        """
        await self.stream_manager.ensure_stream_exists()
        self.js_subscription = await self.js.subscribe(
            self.subject, cb=self.message_handler, stream=self.stream_manager.stream_name, queue=self.queue_group
        )
        logger.debug(f"Subscribed to '{self.subject}' with {self.stream_manager} and queue group '{self.queue_group}'.")

    async def stop(self):
        """Unsubscribes from the JetStream subject, stopping the flow of messages."""
        if self.js_subscription:
            await self.js_subscription.unsubscribe()

    async def message_handler(self, msg):
        """
        Processes incoming messages. Creates a task to handle the message
        processing and acknowledgment asynchronously without blocking.
        """
        try:
            logger.debug(f"Received message: {msg.subject} with event data: {msg.data}")
            topic = Topic.from_subject(msg.subject)
            event_data = msg.data
            event = self.event_cls.deserialize_event(event_data, agent_config_type=self.agent_config_type)
            event._jetstream_sequence = msg.metadata.sequence.stream
            logger.debug(f"Deserialized event: {event}")
            await msg.ack()
            asyncio.create_task(self._process(event, topic, msg))
        except MsgAlreadyAckdError:
            pass
        except Exception as e:
            logger.exception(e)
            logger.exception(f"Error in message handler for subject '{msg.subject}': {e}")

    async def _process(self, event, topic, msg):
        """
        Process the event and acknowledge the message based on result.
        Uses a semaphore to limit the number of concurrent processing.
        """
        async with JSSubscriber._process_semaphore:
            try:
                await self.handler(event, topic)
            except Exception as e:
                logger.exception(e)
                logger.exception(f"Error in async processor for subject '{msg.subject}': {e}")
