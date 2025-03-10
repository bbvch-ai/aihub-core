import asyncio
import logging
import traceback
from typing import Awaitable, Callable, Generic, Optional, Type, TypeVar

from nats.aio.client import Client as NATS
from nats.errors import MsgAlreadyAckdError
from nats.js import JetStreamContext

from aihub_lib.nats.events import BaseEvent, ControlEvent
from aihub_lib.nats.streams.StreamManager import StreamManager
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topics import Topic
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class JSSubscriber(Generic[TEvent]):
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
    - **Topic Parsing:** Transforms the NATS subject into a structured `AgentTopic` for context-aware handling.
    - **Queue Groups:** Allows multiple subscribers to share a single queue, distributing load.

    ### Example
    Use `for_all_agent_events` to subscribe to all events from all agents in a durable manner. If a
    subscriber crashes, events remain in JetStream and can be reprocessed by another subscriber in the queue group.
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
        event_cls: Type[TEvent],
        handler: Callable[[TEvent, Topic], Awaitable[None]],
        js: Optional[JetStreamContext] = None,
    ):
        self.nc = nc
        self.js = js or nc.jetstream()
        self.subject = subject
        self.queue_group = queue_group
        self.stream_manager = StreamManager(self.js, stream_name, stream_subject)
        self.js_subscription: Optional[JetStreamContext.PushSubscription] = None
        self.event_cls = event_cls
        self.handler = handler

    async def start(self):
        """
        Ensures the agent stream exists and subscribes to the subject with the given queue group.
        Once started, the subscriber begins consuming messages from JetStream.
        """
        await self.stream_manager.ensure_agent_stream_exists()
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
            topic = AgentTopic.from_subject(msg.subject)
            event_data = msg.data
            event = self.event_cls.deserialize_event(event_data)
            logger.debug(f"Deserialized event: {event}")
            await msg.ack()
            asyncio.create_task(self._process(event, topic, msg))
        except MsgAlreadyAckdError:
            pass
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            traceback.print_exc()

    async def _process(self, event, topic, msg):
        """
        Process the event and acknowledge the message based on result.
        Uses a semaphore to limit the number of concurrent processing.
        """
        async with JSSubscriber._process_semaphore:
            try:
                await self.handler(event, topic)
            except Exception as e:
                logger.error(f"Error in async handler: {e}")
                traceback.print_exc()

    @classmethod
    def for_agent_instance_events(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[ControlEvent, Topic], Awaitable[None]],
        queue_group: str,
        js: Optional[JetStreamContext] = None,
    ):
        """Subscribe to all control events within a specific agent instance."""
        subject = topic_manager.get_subject_for_everything_within_agent_instance()
        stream_name, stream_subject = topic_manager.get_stream_over_agent()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
        )

    @classmethod
    def for_agent_instance_control_events(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[ControlEvent, Topic], Awaitable[None]],
        queue_group: str,
        js: Optional[JetStreamContext] = None,
    ):
        """Subscribe to all control events within a specific agent instance."""
        subject = topic_manager.get_subject_for_all_control_events_within_agent_instance()
        stream_name, stream_subject = topic_manager.get_stream_over_agent()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
        )
