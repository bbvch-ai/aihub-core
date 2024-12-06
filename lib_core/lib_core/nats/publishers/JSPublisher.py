import logging
from typing import TypeVar, Generic

from nats.js import JetStreamContext

from lib_core.nats.events import BaseEvent

logger = logging.getLogger(__name__)

TEvent = TypeVar('TEvent', bound=BaseEvent)


class JSPublisher(Generic[TEvent]):
    def __init__(self, js: JetStreamContext):
        self.js = js

    async def publish_event(self, event: TEvent, subject: str):
        logger.debug(f"Publishing event {event.__class__.__name__} to {subject}")
        logger.debug(f"Serialized event: {event.model_dump_json()}")
        await self.js.publish(subject, event.model_dump_json().encode())
