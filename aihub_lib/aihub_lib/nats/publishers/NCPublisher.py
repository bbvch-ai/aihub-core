import logging

from nats.aio.client import Client as NATS

from aihub_lib.nats.publishers.AbstractPublisher import AbstractPublisher, TEvent

logger = logging.getLogger(__name__)


class NCPublisher(AbstractPublisher):
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

    def __init__(self, nc: NATS):
        self.nc = nc

    async def publish_event(self, event: TEvent, subject: str):
        """
        Publishes the given event to the specified subject, encoding it as JSON.

        Logs details, warns if there's a mismatch between event type and subject pattern,
        and then sends the message through the NATS client.
        """
        self._detect_and_log_subject_mismatch(event, subject)

        logger.debug(f"Publishing event {event.event_name} to {subject}")
        serialized_event = event.model_dump_json(serialize_as_any=True)
        logger.debug(f"Serialized event: {event.event_name}({serialized_event})")

        await self.nc.publish(subject, serialized_event.encode())
