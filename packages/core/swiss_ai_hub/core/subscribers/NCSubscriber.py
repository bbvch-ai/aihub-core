import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import BadSubscriptionError, ConnectionDrainingError
from opentelemetry import context, trace

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer
from swiss_ai_hub.core.subscribers.AbstractSubscriber import AbstractSubscriber, TEvent
from swiss_ai_hub.core.topics import Topic
from swiss_ai_hub.core.tracing.NATSTraceContextPropagator import NATSTraceContextPropagator

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
        name: Annotated[str, "Name of the subscriber shown in otel"],
        nc: Annotated[NATS, "NATS client"],
        subject: Annotated[str, "NATS subject to subscribe to"],
        event_cls: Annotated[type[TEvent], "Event class to handle in the event handler"],
        handler: Annotated[Callable[[TEvent, Topic], Awaitable[None]], "Event handler"],
    ):
        super().__init__(name, nc, subject, event_cls, handler, protocol="NATS")
        self.subscription: Subscription | None = None

    async def start(self) -> None:
        """Subscribe to the configured subject and begin receiving messages."""
        self.subscription = await self.nc.subscribe(self.subject, cb=self.message_handler)
        logger.debug(f"{self.name} subscribed to '{self.subject}'.")

    async def stop(self) -> None:
        """Unsubscribe from the subject, stopping incoming messages."""
        if self.subscription:
            try:
                await self.subscription.unsubscribe()
                logger.debug(f"{self.name} unsubscribed from '{self.subject}'.")
            except (BadSubscriptionError, ConnectionDrainingError):
                logger.debug(f"{self.name} subscription '{self.subject}' was already unsubscribed.")

    async def message_handler(self, msg: Msg) -> None:
        """
        Handle incoming messages. Deserializes the event, parses the subject into a Topic,
        and calls the handler without blocking.
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
                "messaging.system": "nats",
                "messaging.source": msg.subject,
                "messaging.operation": "receive",
            },
        ) as span:
            try:
                logger.debug(f"{self.name} received message: {msg.subject}")
                topic = Topic.from_subject(msg.subject)
                event_data = msg.data
                event = self.event_cls.deserialize_event(event_data)

                span.update_name(f"{self.name}.receive {event.__class__.__name__}")
                span.set_attribute("event.type", event.event_name)
                span.set_attribute("event.class", event.__class__.__name__)

                logger.debug(f"{self.name} deserialized event: {event.event_name}")
                task = asyncio.create_task(self._run_handler_with_error_handling(event, topic, msg.subject))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

                span.set_attribute("messaging.success", True)

            except Exception as e:
                span.set_attribute("messaging.success", False)
                span.record_exception(e)
                logger.exception(f"{self.name} error in message handler for subject '{msg.subject}': {e}")

    async def _run_handler_with_error_handling(self, event, topic, subject):
        """Helper method to run handler with proper error handling"""
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(
            f"{self.name}.process {event.event_name}",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                "handler.event_type": event.event_name,
                "handler.subject": subject,
            },
        ) as span:
            try:
                await self.handler(event, topic)
                span.set_attribute("handler.success", True)
            except Exception as e:
                span.set_attribute("handler.success", False)
                span.record_exception(e)
                logger.exception(f"{self.name} error in async handler for subject '{subject}': {e}")
