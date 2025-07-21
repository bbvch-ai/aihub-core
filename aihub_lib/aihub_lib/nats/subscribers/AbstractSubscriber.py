import abc
import asyncio
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

from nats.aio.client import Client as NATS

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.topics import Topic

TEvent = TypeVar("TEvent", bound=BaseEvent)


class AbstractSubscriber(Generic[TEvent], abc.ABC):
    def __init__(
        self,
        nc: NATS,
        subject: str,
        event_cls: type[TEvent],
        handler: Callable[[TEvent, Topic], Awaitable[None]],
    ):
        self.nc = nc
        self.subject = subject
        self.event_cls = event_cls
        self.handler = handler

        self._background_tasks: set[asyncio.Task] = set()

    @abc.abstractmethod
    async def start(self) -> None:
        pass

    @abc.abstractmethod
    async def stop(self) -> None:
        pass

    @abc.abstractmethod
    async def message_handler(self, msg):
        pass
