import asyncio
import logging
import uuid
from typing import Generic, TypeVar, Annotated

from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_lib.nats.events import BaseEvent, ControlEvent, DisplayEvent
from aihub_lib.nats.topic_managers.TopicManager import TopicManager

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class JSPublisher(Generic[TEvent]):
    """
    A publisher that integrates with NATS JetStream, ensuring events are stored in streams
    for durability, replay, and at-least-once delivery semantics.

    ### Why JSPublisher?
    While NCPublisher publishes events to ephemeral subjects, JSPublisher leverages JetStream.
    By publishing events via `js.publish`, messages are persisted according to stream configurations.
    This is essential for systems that need guaranteed message retention, auditing, or replaying.

    ### Features
    - **Durable Storage:** Events are written to JetStream-managed streams.
    - **Type-Awareness & Logging:** Similar to NCPublisher, it logs events, checks event-subject alignment,
      and warns if, for example, a control event is published to a display subject.
    """

    def __init__(
            self,
            js: JetStreamContext,
            redis: Redis,
            default_ttl: Annotated[int, "How long to store event info in redis"] = 60 * 60, # 1 hour in seconds
    ):
        self.js = js
        self.redis = redis
        self.default_ttl = default_ttl

    async def publish_event(self, event: TEvent, subject: str, retries=10):
        """
        Publishes the given event to the specified JetStream subject, encoding it as JSON.

        Logs event details and warns if event type does not match the subject pattern.
        This ensures developers can catch configuration issues early and maintain consistent
        event routing conventions.
        """
        logger.debug(f"Publishing event {event.__class__.__name__} to {subject}")
        serialized_event = event.model_dump_json(serialize_as_any=True)
        logger.debug(f"Serialized event: {event.__class__.__name__}")

        await self.redis.set(subject, serialized_event, ex=self.default_ttl)

        if f".{TopicManager.CONTROL_EVENT}." in subject and not isinstance(event, ControlEvent):
            logger.warning(
                f"Control event {event.__class__.__name__} is being published to a non-control subject: {subject}"
            )

        if f".{TopicManager.DISPLAY_EVENT}." in subject and not isinstance(event, DisplayEvent):
            logger.warning(
                f"Display event {event.__class__.__name__} is being published to a non-display subject: {subject}"
            )

        message_id = str(uuid.uuid4())
        headers = {"Nats-Msg-Id": message_id}  # Deduplication

        for attempt in range(retries):
            try:
                future = await asyncio.wait_for(
                    self.js.publish_async(subject, serialized_event.encode(), headers=headers), timeout=5
                )
                ack = await asyncio.wait_for(future, timeout=5)
                logger.debug(f"Publish ACK received: {ack}")
                return  # Success, no retry needed
            except asyncio.TimeoutError:
                logger.warning(f"Publish timeout ({attempt + 1}/{retries}) for {event.__class__.__name__}")
            except Exception as e:
                logger.error(f"NATS error while publishing event: {e}")

            await asyncio.sleep(1)  # Wait before retrying

        logger.error(f"Failed to publish event {event.__class__.__name__} after {retries} attempts")
