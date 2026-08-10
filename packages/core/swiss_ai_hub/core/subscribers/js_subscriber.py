import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from nats.aio.client import Client as NATS
from nats.errors import MsgAlreadyAckdError
from nats.errors import TimeoutError as NatsTimeoutError
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig
from nats.js.errors import APIError, NotFoundError
from opentelemetry import context, trace

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import get_tracer
from swiss_ai_hub.core.streams.stream_manager import StreamManager
from swiss_ai_hub.core.subscribers.abstract_subscriber import AbstractSubscriber, TEvent
from swiss_ai_hub.core.topics import Topic
from swiss_ai_hub.core.tracing.nats_message_headers import NATSMessageHeaders
from swiss_ai_hub.core.tracing.nats_trace_context_propagator import NATSTraceContextPropagator

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

    DEFAULT_ACK_WAIT_SECONDS: float = 30.0
    DEFAULT_MAX_DELIVER: int = 5

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
        ack_wait: Annotated[
            float, "Seconds the server waits for an ack before redelivering"
        ] = DEFAULT_ACK_WAIT_SECONDS,
        max_deliver: Annotated[int, "Maximum delivery attempts per message"] = DEFAULT_MAX_DELIVER,
    ):
        super().__init__(name, nc, subject, event_cls, handler, protocol="JetStream")
        self.js = js or nc.jetstream()
        self.queue_group = queue_group
        self.ack_wait = ack_wait
        self.max_deliver = max_deliver
        self.stream_manager = StreamManager(self.js, stream_name, stream_subject)
        self.js_subscription: JetStreamContext.PushSubscription | None = None

    async def start(self):
        """
        Ensures the stream exists and subscribes to the subject with the given queue group.
        Once started, the subscriber begins consuming messages from JetStream.
        """
        await self.stream_manager.ensure_stream_exists()
        await self._ensure_consumer_config()
        self.js_subscription = await self.js.subscribe(
            subject=self.subject,
            cb=self.message_handler,
            stream=self.stream_manager.stream_name,
            queue=self.queue_group,
            config=ConsumerConfig(ack_wait=self.ack_wait, max_deliver=self.max_deliver),
        )
        logger.debug(
            f"{self.name} subscribed to '{self.subject}' with {self.stream_manager} "
            f"and queue group '{self.queue_group}'."
        )

    async def _ensure_consumer_config(self) -> None:
        """
        nats-py binds to an existing durable consumer with its server-side config, silently ignoring
        the config passed to subscribe. Redelivery settings drift on already-deployed consumers is
        therefore corrected here, before subscribing.
        """
        try:
            consumer_info = await self.js.consumer_info(self.stream_manager.stream_name, self.queue_group)
        except NotFoundError:
            # NotFoundError is how nats-py answers "does this consumer exist?" — there is no
            # exists() call. Nothing to reconcile on a first deployment; subscribe() creates the
            # consumer with the config it is passed. Any other failure propagates.
            logger.debug(
                f"{self.name} found no existing consumer '{self.queue_group}' on stream "
                f"'{self.stream_manager.stream_name}'; subscribe will create it"
            )
            return

        consumer_config = consumer_info.config
        if consumer_config.ack_wait == self.ack_wait and consumer_config.max_deliver == self.max_deliver:
            logger.debug(
                f"{self.name} consumer '{self.queue_group}' already at "
                f"ack_wait={self.ack_wait}s max_deliver={self.max_deliver}"
            )
            return

        consumer_config.ack_wait = self.ack_wait
        consumer_config.max_deliver = self.max_deliver
        try:
            await self.js.add_consumer(self.stream_manager.stream_name, config=consumer_config)
        except (APIError, NatsTimeoutError):
            # Reconciling redelivery settings is best-effort. The consumer already exists and keeps
            # consuming with its current config, so a failure here degrades to the behaviour that was
            # in place before this call — not a reason to refuse to start and take the whole service
            # down with it. Programming errors still propagate; only JetStream API and transport
            # failures are tolerated.
            logger.warning(
                f"{self.name} could not update consumer '{self.queue_group}' to "
                f"ack_wait={self.ack_wait}s max_deliver={self.max_deliver}; "
                f"continuing with its existing redelivery settings",
                exc_info=True,
            )
            return

        logger.info(
            f"{self.name} updated consumer '{self.queue_group}' to "
            f"ack_wait={self.ack_wait}s max_deliver={self.max_deliver}"
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
                event._aihub_headers = NATSMessageHeaders.extract_aihub_headers(headers)

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
