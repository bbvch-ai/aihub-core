import logging
from typing import Generic, TypeVar

from nats.aio.client import Client as NATS

from lib_core.nats.events import BaseEvent

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class NCPublisher(Generic[TEvent]):
    def __init__(self, nc: NATS):
        self.nc = nc

    async def publish_event(self, event: TEvent, subject: str):
        logger.debug(f"Publishing event {event.__class__.__name__} to {subject}")
        logger.debug(f"Serialized event: {event.model_dump_json()}")
        await self.nc.publish(subject, event.model_dump_json().encode())
