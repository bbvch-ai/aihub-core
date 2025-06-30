import abc
from typing import Awaitable, Callable, Generic, Type, TypeVar

from nats.aio.client import Client as NATS

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.topics import Topic

TEvent = TypeVar("TEvent", bound=BaseEvent)


class AbstractSubscriber(Generic[TEvent], abc.ABC):
    def __init__(
        self,
        nc: NATS,
        subject: str,
        event_cls: Type[TEvent],
        handler: Callable[[TEvent, Topic], Awaitable[None]],
    ):
        self.nc = nc
        self.subject = subject
        self.event_cls = event_cls
        self.handler = handler

    @abc.abstractmethod
    async def start(self) -> None:
        pass

    @abc.abstractmethod
    async def stop(self) -> None:
        pass

    @abc.abstractmethod
    async def message_handler(self, msg):
        pass
