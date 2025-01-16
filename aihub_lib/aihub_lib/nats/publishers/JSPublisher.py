import logging
from typing import Generic, TypeVar

from nats.js import JetStreamContext

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

    def __init__(self, js: JetStreamContext):
        self.js = js

    async def publish_event(self, event: TEvent, subject: str):
        """
        Publishes the given event to the specified JetStream subject, encoding it as JSON.

        Logs event details and warns if event type does not match the subject pattern.
        This ensures developers can catch configuration issues early and maintain consistent
        event routing conventions.
        """
        logger.debug(f"Publishing event {event.__class__.__name__} to {subject}")
        logger.debug(f"Serialized event: {event.model_dump_json()}")

        if f".{TopicManager.CONTROL_EVENT}." in subject and not isinstance(event, ControlEvent):
            logger.warning(
                f"Control event {event.__class__.__name__} is being published to a non-control subject: {subject}"
            )

        if f".{TopicManager.DISPLAY_EVENT}." in subject and not isinstance(event, DisplayEvent):
            logger.warning(
                f"Display event {event.__class__.__name__} is being published to a non-display subject: {subject}"
            )

        await self.js.publish(subject, event.model_dump_json().encode())
