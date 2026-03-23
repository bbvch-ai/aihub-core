import logging
from typing import Annotated

from nats.aio.client import Client as NATS

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import get_tracer
from swiss_ai_hub.core.publishers.abstract_publisher import AbstractPublisher, TEvent
from swiss_ai_hub.core.tracing.nats_message_headers import NATSMessageHeaders

logger = logging.getLogger(__name__)


class NCPublisher(AbstractPublisher[TEvent]):
    """
    A generic publisher for sending typed events to NATS subjects.

    ### Why NCPublisher?
    This class provides a clear, type-safe way to publish serialized event objects to NATS.
    It adds logging and basic sanity checks to ensure the event type aligns with the
    subject's intent (e.g., control events to control subjects).

    ### Features
    - **Type Safety:** The publisher is generic over TEvent, making it explicit what kind of events
      can be published through a particular instance.
    - **Logging & Validation:** Before publishing, it logs the event and checks that the event type
      matches the subject pattern (control vs. display). This helps catch configuration errors or
      inconsistent naming conventions early.
    """

    def __init__(
        self,
        name: Annotated[str, "Name of the publisher shown in otel"],
        nc: Annotated[NATS, "NATS client"],
    ):
        super().__init__(name, protocol="NATS")
        self.nc = nc

    async def publish_event(self, event: TEvent, subject: str):
        """
        Publishes the given event to the specified subject, encoding it as JSON.

        Logs details, warns if there's a mismatch between event type and subject pattern,
        and then sends the message through the NATS client.
        """
        tracer = get_tracer(__name__)

        with tracer.start_as_current_span(
            f"{self.name}.publish {event.__class__.__name__}",
            attributes={
                "messaging.system": "nats",
                "messaging.destination": subject,
                "messaging.operation": "publish",
                "event.type": event.event_name,
                "event.class": event.__class__.__name__,
            },
        ) as span:
            try:
                self._detect_and_log_subject_mismatch(event, subject)

                logger.debug(f"{self.name} publishing event {event.event_name} to {subject}")
                serialized_event = event.model_dump_json(serialize_as_any=True)
                logger.debug(f"{self.name} serialized event: {event.event_name}")

                headers = NATSMessageHeaders().with_trace_context().to_dict()

                await self.nc.publish(subject, serialized_event.encode(), headers=headers)

                span.set_attribute("messaging.success", True)
                logger.debug(f"{self.name} successfully published {event.event_name} to {subject}")

            except Exception as e:
                span.set_attribute("messaging.success", False)
                span.record_exception(e)
                logger.exception(f"{self.name} failed to publish {event.event_name} to {subject}: {e}")
                raise
