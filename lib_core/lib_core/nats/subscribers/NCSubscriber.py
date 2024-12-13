import logging
import traceback
from typing import Optional, TypeVar, Generic, Type, Callable, Awaitable

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import BadSubscriptionError

from lib_core.nats.events import BaseEvent, DisplayEvent, ControlEvent
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import (
    AgentThreadTopicManager,
)
from lib_core.nats.topics import Topic
from lib_core.nats.topics.agents.AgentTopic import AgentTopic

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class NCSubscriber(Generic[TEvent]):
    def __init__(
        self,
        nc: NATS,
        subject: str,
        event_cls: Type[TEvent],
        handler: Callable[[TEvent, Topic], Awaitable[None]],
    ):
        self.nc = nc
        self.subject = subject
        self.subscription: Optional[Subscription] = None
        self.event_cls = event_cls
        self.handler = handler

    async def start(self) -> None:
        self.subscription = await self.nc.subscribe(self.subject, cb=self.message_handler)
        logger.debug(f"Subscribed to '{self.subject}'.")

    async def stop(self) -> None:
        if self.subscription:
            try:
                await self.subscription.unsubscribe()
                logger.debug(f"Unsubscribed from '{self.subject}'.")
            except BadSubscriptionError:
                logger.debug(f"Subscription '{self.subject}' already unsubscribed.")

    async def message_handler(self, msg: Msg) -> None:
        try:
            logger.debug(f"Received message: {msg.subject} with event data: {msg.data!r}")
            topic = Topic.from_subject(msg.subject)
            event_data = msg.data
            event = self.event_cls.deserialize_event(event_data)
            logger.debug(f"Deserialize event: {event}")
            await self.handler(event, topic)
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            traceback.print_exc()

    @classmethod
    def for_all_agent_control_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[DisplayEvent, Topic], Awaitable[None]],
    ):
        subject = topic_manager.get_subject_for_all_control_events_in_agent()
        return cls(
            nc=nc,
            subject=subject,
            event_cls=DisplayEvent,
            handler=handler,
        )

    @classmethod
    def all_for_agent_display_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[DisplayEvent, Topic], Awaitable[None]],
    ):
        subject = topic_manager.get_subject_for_all_display_events_in_agent()
        return cls(
            nc=nc,
            subject=subject,
            event_cls=DisplayEvent,
            handler=handler,
        )

    @classmethod
    def for_thread_display_events(
        cls,
        nc: NATS,
        topic_manager: AgentThreadTopicManager,
        handler: Callable[[DisplayEvent, Topic], Awaitable[None]],
    ):
        subject = topic_manager.get_subject_for_display_event_in_thread("*", "*")
        return cls(
            nc=nc,
            subject=subject,
            event_cls=DisplayEvent,
            handler=handler,
        )

    @classmethod
    def for_thread_control_events(
            cls,
            nc: NATS,
            topic_manager: AgentThreadTopicManager,
            handler: Callable[[ControlEvent, Topic], Awaitable[None]],
    ):
        subject = topic_manager.get_subject_for_control_event_in_thread("*", "*")
        return cls(
            nc=nc,
            subject=subject,
            event_cls=DisplayEvent,
            handler=handler,
        )

    @classmethod
    def for_all_thread_events(
            cls,
            nc: NATS,
            topic_manager: AgentThreadTopicManager,
            handler: Callable[[ControlEvent, Topic], Awaitable[None]],
    ):
        subject = topic_manager.get_subject_for_all_event_in_thread("*", "*")
        return cls(
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_agent_discovery_request_events(
            cls,
            nc: NATS,
            topic_manager: TopicManager,
            handler: Callable[[BaseEvent, Topic], Awaitable[None]],
            call_id: str = "*",
    ):
        subject = topic_manager.get_agent_discovery_subject_request(call_id)
        return cls(
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_agent_discovery_response_events(
            cls,
            nc: NATS,
            topic_manager: TopicManager,
            handler: Callable[[BaseEvent, Topic], Awaitable[None]],
            call_id: str = "*",
    ):
        subject = topic_manager.get_agent_discovery_subject_response(call_id)
        return cls(
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )