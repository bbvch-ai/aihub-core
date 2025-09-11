import asyncio
import logging
from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import BadSubscriptionError, ConnectionDrainingError
from opentelemetry import context, trace

from aihub_lib.nats.subscribers.AbstractSubscriber import AbstractSubscriber, TEvent
from aihub_lib.nats.topics import Topic
from aihub_lib.nats.tracing.NATSTraceContextPropagator import NATSTraceContextPropagator

logger = logging.getLogger(__name__)


class NCSubscriber(AbstractSubscriber[TEvent]):
    """
    A generic NATS subscriber that reads messages from a given subject and delegates handling
    to a provided async callback. It deserializes event data into a specified event class (TEvent)
    and also parses the message subject into a Topic object for further context.

    ### Why NCSubscriber?
    In an event-driven architecture, you often subscribe to subjects and process incoming messages.
    By standardizing subscription logic (e.g., handling unsubscribes, parsing topics, deserializing events),
    NCSubscriber simplifies consumers and ensures consistent error handling and logging.

    ### Key Features
    - **Generic Event Handling:** You provide a TEvent type, and the subscriber automatically
      deserializes the data according to that event type.
    - **Topic Parsing:** The subscriber uses `Topic.from_subject` to transform the subject into a
      structured Topic object, making it easy for handlers to understand the origin and scope of the event.
    - **Lifecycle Management:** `start()` and `stop()` methods manage the subscription lifecycle,
      including safe unsubscription.
    """

    def __init__(
        self,
        nc: NATS,
        subject: str,
        event_cls: type[TEvent],
        handler: Callable[[TEvent, Topic], Awaitable[None]],
    ):
        super().__init__(nc, subject, event_cls, handler)
        self.subscription: Subscription | None = None

    async def start(self) -> None:
        """Subscribe to the configured subject and begin receiving messages."""
        self.subscription = await self.nc.subscribe(self.subject, cb=self.message_handler)
        logger.debug(f"Subscribed to '{self.subject}'.")

    async def stop(self) -> None:
        """Unsubscribe from the subject, stopping incoming messages."""
        if self.subscription:
            try:
                await self.subscription.unsubscribe()
                logger.debug(f"Unsubscribed from '{self.subject}'.")
            except (BadSubscriptionError, ConnectionDrainingError):
                logger.debug(f"Subscription '{self.subject}' was already unsubscribed.")

    async def message_handler(self, msg: Msg) -> None:
        """
        Handle incoming messages. Deserializes the event, parses the subject into a Topic,
        and calls the handler without blocking.
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
            f"NATs.receive {msg.subject}", context=parent_context, kind=trace.SpanKind.CONSUMER
        ) as span:
            span.set_attribute("messaging.system", "nats")
            span.set_attribute("messaging.source", msg.subject)
            span.set_attribute("messaging.operation", "receive")

            try:
                logger.debug(f"Received message: {msg.subject} with event data: {msg.data!r}")
                topic = Topic.from_subject(msg.subject)
                event_data = msg.data
                event = self.event_cls.deserialize_event(event_data)

                span.set_attribute("event.type", event.event_name)
                span.set_attribute("event.class", event.__class__.__name__)

                logger.debug(f"Deserialized event: {event}")
                task = asyncio.create_task(self._run_handler_with_error_handling(event, topic, msg.subject))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

                span.set_attribute("messaging.success", True)

            except Exception as e:
                span.set_attribute("messaging.success", False)
                span.record_exception(e)
                logger.exception(f"Error in message handler for subject '{msg.subject}': {e}")

    async def _run_handler_with_error_handling(self, event, topic, subject):
        """Helper method to run handler with proper error handling"""
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(f"NATs.process {event.event_name}", kind=trace.SpanKind.INTERNAL) as span:
            span.set_attribute("handler.event_type", event.event_name)
            span.set_attribute("handler.subject", subject)

            try:
                await self.handler(event, topic)
                span.set_attribute("handler.success", True)
            except Exception as e:
                span.set_attribute("handler.success", False)
                span.record_exception(e)
                logger.exception(f"Error in async handler for subject '{subject}': {e}")
