import abc
import asyncio
from collections.abc import Awaitable, Callable
from typing import Annotated, Literal, TypeVar

from nats.aio.client import Client as NATS

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.topics import Topic

# TypeVar for backward compatibility with existing imports
TEvent = TypeVar("TEvent", bound=BaseEvent)


class AbstractSubscriber[TEvent: BaseEvent](abc.ABC):
    def __init__(
        self,
        name: Annotated[str, "Name of the subscriber shown in otel"],
        nc: Annotated[NATS, "NATS client"],
        subject: Annotated[str, "NATS subject to subscribe to"],
        event_cls: Annotated[type[TEvent], "Event class to handle in the event handler"],
        handler: Annotated[Callable[[TEvent, Topic], Awaitable[None]], "Event handler"],
        protocol: Annotated[Literal["JetStream", "NATS"], "Protocol used to publish events, either JetStream or NATS"],
    ):
        self.name = name if name.endswith(f"{protocol}Subscriber") else f"{name}{protocol}Subscriber"
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
