import logging
from typing import TypeVar, Generic

from nats.js import JetStreamContext

from lib_core.nats.events import BaseEvent, ControlEvent, DisplayEvent
from lib_core.nats.topic_managers.TopicManager import TopicManager

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class JSPublisher(Generic[TEvent]):
    def __init__(self, js: JetStreamContext):
        self.js = js

    async def publish_event(self, event: TEvent, subject: str):
        logger.debug(f"Publishing event {event.__class__.__name__} to {subject}")
        logger.debug(f"Serialized event: {event.model_dump_json()}")

        if f".{TopicManager.CONTROL_EVENT}." in subject and not isinstance(event, ControlEvent):
            logger.warning(f"Control event {event.__class__.__name__} is being published to a non-control subject: {subject}")

        if f".{TopicManager.DISPLAY_EVENT}." in subject and not isinstance(event, DisplayEvent):
            logger.warning(f"Display event {event.__class__.__name__} is being published to a non-display subject: {subject}")

        await self.js.publish(subject, event.model_dump_json().encode())
