import asyncio
import logging
from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS
from nats.errors import MsgAlreadyAckdError
from nats.js import JetStreamContext
from opentelemetry import context, trace

from aihub_lib.nats.streams.StreamManager import StreamManager
from aihub_lib.nats.subscribers.AbstractSubscriber import AbstractSubscriber, TEvent
from aihub_lib.nats.topics import Topic
from aihub_lib.nats.tracing.NATSTraceContextPropagator import NATSTraceContextPropagator

logger = logging.getLogger(__name__)


class JSSubscriber(AbstractSubscriber[TEvent]):
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
    ):
        super().__init__(nc, subject, event_cls, handler)
        self.js = js or nc.jetstream()
        self.queue_group = queue_group
        self.stream_manager = StreamManager(self.js, stream_name, stream_subject)
        self.js_subscription: JetStreamContext.PushSubscription | None = None

    async def start(self):
        """
        Ensures the stream exists and subscribes to the subject with the given queue group.
        Once started, the subscriber begins consuming messages from JetStream.
        """
        await self.stream_manager.ensure_stream_exists()
        self.js_subscription = await self.js.subscribe(
            subject=self.subject,
            cb=self.message_handler,
            stream=self.stream_manager.stream_name,
            queue=self.queue_group,
        )
        logger.debug(f"Subscribed to '{self.subject}' with {self.stream_manager} and queue group '{self.queue_group}'.")

    async def stop(self):
        """Unsubscribes from the JetStream subject, stopping the flow of messages."""
        if self.js_subscription:
            await self.js_subscription.unsubscribe()
        logger.debug(
            f"Unsubscribed from '{self.subject}' with {self.stream_manager} and queue group '{self.queue_group}'."
        )

    async def message_handler(self, msg):
        """
        Processes incoming messages. Creates a task to handle the message
        processing and acknowledgment asynchronously without blocking.
        """
        tracer = trace.get_tracer(__name__)

        # Extract trace context from headers
        headers = getattr(msg, "headers", {}) or {}
        parent_context = context.get_current()

        if headers:
            try:
                parent_context = NATSTraceContextPropagator.extract_and_activate_trace_context(headers)
            except Exception as e:
                logger.warning(f"Failed to extract trace context from headers: {e}")

        with tracer.start_as_current_span(
            f"JetStream.receive {msg.subject}", context=parent_context, kind=trace.SpanKind.CONSUMER
        ) as span:
            span.set_attribute("messaging.system", "nats.jetstream")
            span.set_attribute("messaging.source", msg.subject)
            span.set_attribute("messaging.operation", "receive")
            span.set_attribute("jetstream.stream", self.stream_manager.stream_name)
            span.set_attribute("jetstream.queue_group", self.queue_group)

            if hasattr(msg, "metadata") and msg.metadata:
                span.set_attribute("jetstream.sequence", msg.metadata.sequence.stream)
                if hasattr(msg.metadata, "num_delivered"):
                    span.set_attribute("jetstream.delivery_count", msg.metadata.num_delivered)

            try:
                logger.debug(f"Received message: {msg.subject} with event data: {msg.data}")
                topic = Topic.from_subject(msg.subject)
                event_data = msg.data
                event = self.event_cls.deserialize_event(event_data)
                event._jetstream_sequence = msg.metadata.sequence.stream  # CRITICAL: Keep this!

                span.set_attribute("event.type", event.event_name)
                span.set_attribute("event.class", event.__class__.__name__)

                logger.debug(f"Deserialized event: {event}")

                await msg.ack()
                span.set_attribute("jetstream.acked", True)

                task = asyncio.create_task(self._process(event, topic, msg))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

                span.set_attribute("messaging.success", True)

            except MsgAlreadyAckdError:
                span.set_attribute("jetstream.acked", False)
                span.add_event("Message already acknowledged")
            except Exception as e:
                span.set_attribute("messaging.success", False)
                span.record_exception(e)
                logger.exception(f"Error in message handler for subject '{msg.subject}': {e}")

    async def _process(self, event, topic, msg):
        """
        Process the event and acknowledge the message based on result.
        Uses a semaphore to limit the number of concurrent processing.
        """
        tracer = trace.get_tracer(__name__)

        async with JSSubscriber._process_semaphore:
            with tracer.start_as_current_span(
                f"JetStream.process {event.event_name}", kind=trace.SpanKind.INTERNAL
            ) as span:
                span.set_attribute("handler.event_type", event.event_name)
                span.set_attribute("handler.subject", msg.subject)
                span.set_attribute("jetstream.processing", True)

                try:
                    await self.handler(event, topic)
                    span.set_attribute("handler.success", True)
                except Exception as e:
                    span.set_attribute("handler.success", False)
                    span.record_exception(e)
                    logger.exception(f"Error in async processor for subject '{msg.subject}': {e}")
