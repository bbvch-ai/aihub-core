import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from nats.aio.client import Client as NATS
from nats.errors import MsgAlreadyAckdError
from nats.js import JetStreamContext
from opentelemetry import context, trace

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer
from swiss_ai_hub.core.streams.StreamManager import StreamManager
from swiss_ai_hub.core.subscribers.AbstractSubscriber import AbstractSubscriber, TEvent
from swiss_ai_hub.core.topics import Topic
from swiss_ai_hub.core.tracing.NATSTraceContextPropagator import NATSTraceContextPropagator

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
        name: Annotated[str, "Name of the subscriber shown in otel"],
        nc: Annotated[NATS, "NATS client"],
        subject: Annotated[str, "NATS subject to subscribe to"],
        stream_name: Annotated[str, "JetStream stream name, must be globally unique"],
        stream_subject: Annotated[str, "Subject this JetStream stream is bound to"],
        queue_group: Annotated[str, "Name of group that shares the responsibility to handle events in this stream"],
        event_cls: Annotated[type[TEvent], "Event class to handle in the event handler"],
        handler: Annotated[Callable[[TEvent, Topic], Awaitable[None]], "Event handler"],
        js: Annotated[JetStreamContext, "JetStream instance"],
    ):
        super().__init__(name, nc, subject, event_cls, handler, protocol="JetStream")
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
        logger.debug(
            f"{self.name} subscribed to '{self.subject}' with {self.stream_manager} "
            f"and queue group '{self.queue_group}'."
        )

    async def stop(self):
        """Unsubscribes from the JetStream subject, stopping the flow of messages."""
        if self.js_subscription:
            await self.js_subscription.unsubscribe()
        logger.debug(
            f"{self.name} unsubscribed from '{self.subject}' with {self.stream_manager} "
            f"and queue group '{self.queue_group}'."
        )

    async def message_handler(self, msg):
        """
        Processes incoming messages. Creates a task to handle the message
        processing and acknowledgment asynchronously without blocking.
        """
        tracer = get_tracer(__name__)

        headers = getattr(msg, "headers", {}) or {}
        parent_context = context.get_current()

        if headers:
            try:
                parent_context = NATSTraceContextPropagator.extract_and_activate_trace_context(headers)
            except Exception as e:
                logger.warning(f"{self.name} failed to extract trace context from headers: {e}")

        with tracer.start_as_current_span(
            f"{self.name}.receive UNKNOWN",
            context=parent_context,
            kind=trace.SpanKind.CONSUMER,
            attributes={
                "messaging.system": "nats.jetstream",
                "messaging.source": msg.subject,
                "messaging.operation": "receive",
                "jetstream.stream": self.stream_manager.stream_name,
                "jetstream.queue_group": self.queue_group,
            },
        ) as span:
            if hasattr(msg, "metadata") and msg.metadata:
                span.set_attribute("jetstream.sequence", msg.metadata.sequence.stream)
                if hasattr(msg.metadata, "num_delivered"):
                    span.set_attribute("jetstream.delivery_count", msg.metadata.num_delivered)

            try:
                logger.debug(f"{self.name} received message: {msg.subject}")
                topic = Topic.from_subject(msg.subject)
                event_data = msg.data
                event = self.event_cls.deserialize_event(event_data)
                event._jetstream_sequence = msg.metadata.sequence.stream

                span.update_name(f"{self.name}.receive {event.__class__.__name__}")
                span.set_attribute("event.type", event.event_name)
                span.set_attribute("event.class", event.__class__.__name__)

                logger.debug(f"{self.name} deserialized event: {event.event_name}")

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
                logger.exception(f"{self.name} error in message handler for subject '{msg.subject}': {e}")

    async def _process(self, event, topic, msg):
        """
        Process the event and acknowledge the message based on result.
        Uses a semaphore to limit the number of concurrent processing.
        """
        tracer = get_tracer(__name__)

        async with JSSubscriber._process_semaphore:
            with tracer.start_as_current_span(
                f"{self.name}.process {event.event_name}",
                kind=trace.SpanKind.INTERNAL,
                attributes={
                    "handler.event_type": event.event_name,
                    "handler.subject": msg.subject,
                    "jetstream.processing": True,
                },
            ) as span:
                try:
                    await self.handler(event, topic)
                    span.set_attribute("handler.success", True)
                except Exception as e:
                    span.set_attribute("handler.success", False)
                    span.record_exception(e)
                    logger.exception(f"{self.name} error in async processor for subject '{msg.subject}': {e}")
