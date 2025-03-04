import logging
from typing import Generic, TypeVar, Annotated

from nats.aio.client import Client as NATS
from redis.asyncio import Redis

from aihub_lib.nats.events import BaseEvent, ControlEvent, DisplayEvent
from aihub_lib.nats.topic_managers.TopicManager import TopicManager

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class NCPublisher(Generic[TEvent]):
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

    def __init__(self,
                 nc: NATS,
                 redis: Redis,
                 default_ttl: Annotated[int, "How long to store event info in redis"] = 60 * 60,  # 1 hour in seconds

                 ):
        self.nc = nc
        self.redis = redis
        self.default_ttl = default_ttl

    async def publish_event(self, event: TEvent, subject: str):
        """
        Publishes the given event to the specified subject, encoding it as JSON.

        Logs details, warns if there's a mismatch between event type and subject pattern,
        and then sends the message through the NATS client.
        """
        logger.debug(f"Publishing event {event.__class__.__name__} to {subject}")
        serialized_event = event.model_dump_json(serialize_as_any=True)
        logger.debug(f"Serialized event: {event.__class__.__name__}")

        if f".{TopicManager.CONTROL_EVENT}." in subject and not isinstance(event, ControlEvent):
            logger.warning(
                f"Control event {event.__class__.__name__} is being published to a non-control subject: {subject}"
            )

        if f".{TopicManager.DISPLAY_EVENT}." in subject and not isinstance(event, DisplayEvent):
            logger.warning(
                f"Display event {event.__class__.__name__} is being published to a non-display subject: {subject}"
            )

        await self.nc.publish(subject, serialized_event.encode())
