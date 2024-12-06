import logging
import traceback
from typing import Optional, TypeVar, Generic, Type, Callable, Awaitable, Coroutine, Any

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from lib_core.nats.events import BaseEvent, ControlEvent, DisplayEvent
from lib_core.nats.streams.StreamManager import StreamManager
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from lib_core.nats.topics.agents.AgentTopic import AgentTopic

logger = logging.getLogger(__name__)

TEvent = TypeVar('TEvent', bound=BaseEvent)


class JSSubscriber(Generic[TEvent]):
    def __init__(
        self,
        nc: NATS,
        subject: str,
        stream_name: str,
        stream_subject: str,
        queue_group: str,
        event_cls: Type[TEvent],
        handler: Callable[[TEvent, AgentTopic], Awaitable[None]], js: Optional[JetStreamContext] = None,
        ack_on_fail=True,
    ):
        self.nc = nc
        self.js = js or nc.jetstream()
        self.subject = subject
        self.queue_group = queue_group
        self.stream_manager = StreamManager(self.js, stream_name, stream_subject)
        self.js_subscription: Optional[JetStreamContext.PushSubscription] = None
        self.event_cls = event_cls
        self.handler = handler
        self.ack_on_fail = ack_on_fail

    async def start(self):
        await self.stream_manager.ensure_agent_stream_exists()
        self.js_subscription = await self.js.subscribe(
            self.subject,
            cb=self.message_handler,
            queue=self.queue_group
        )
        logger.debug(
            f"Subscribed to '{self.subject}' with stream_manager '{self.stream_manager}' and queue group '{self.queue_group}'.")

    async def stop(self):
        if self.js_subscription:
            await self.js_subscription.unsubscribe()

    async def message_handler(self, msg):
        try:
            logger.debug(f"Received message: {msg.subject} with event data: {msg.data}")
            topic = AgentTopic.from_subject(msg.subject)
            event_data = msg.data
            event = self.event_cls.deserialize_event(event_data)
            logger.debug(f"Deserialize event: {event}")
            await self.handler(event, topic)
            await msg.ack()
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            traceback.print_exc()
            if self.ack_on_fail:
                await msg.ack()

    @classmethod
    def for_all_agent_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[BaseEvent, AgentTopic], Coroutine[Any, Any, None]],
        js: Optional[JetStreamContext] = None,
        ack_on_fail=True,
    ):
        subject = topic_manager.get_subject_for_all_events_in_agent()
        queue_group = topic_manager.get_stream_group_for_all_events_in_agent()

        stream_name = topic_manager.get_stream_name_for_all_events_in_agent()
        stream_subject = topic_manager.get_subject_for_all_events_in_agent()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=BaseEvent,
            handler=handler,
            js=js,
            ack_on_fail=ack_on_fail,
        )

    @classmethod
    def for_all_agent_control_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[ControlEvent, AgentTopic], Coroutine[Any, Any, None]],
        js: Optional[JetStreamContext] = None,
        ack_on_fail=True,
    ):
        subject = topic_manager.get_subject_for_all_control_events_in_agent()
        queue_group = topic_manager.get_stream_group_for_all_control_events_in_agent()

        stream_name = topic_manager.get_stream_name_for_all_events_in_agent()
        stream_subject = topic_manager.get_subject_for_all_events_in_agent()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
            ack_on_fail=ack_on_fail,
        )

    @classmethod
    def all_for_agent_display_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[DisplayEvent, AgentTopic], Coroutine[Any, Any, None]],
        js: Optional[JetStreamContext] = None,
        ack_on_fail=True,
    ):
        subject = topic_manager.get_subject_for_all_display_events_in_agent()
        queue_group = topic_manager.get_stream_group_for_all_display_events_in_agent()

        stream_name = topic_manager.get_stream_name_for_all_events_in_agent()
        stream_subject = topic_manager.get_subject_for_all_events_in_agent()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=DisplayEvent,
            handler=handler,
            js=js,
            ack_on_fail=ack_on_fail
        )

    @classmethod
    def for_agent_instance_control_events(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[ControlEvent, AgentTopic], Coroutine[Any, Any, None]],
        js: Optional[JetStreamContext] = None,
        ack_on_fail=True,
    ):
        subject = topic_manager.get_subject_for_all_control_events_within_agent_instance()
        queue_group = topic_manager.get_stream_group_for_all_control_events_within_agent()

        stream_name = topic_manager.get_stream_name_for_all_events_in_agent()
        stream_subject = topic_manager.get_subject_for_all_events_in_agent()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
            ack_on_fail=ack_on_fail,
        )

    @classmethod
    def for_agent_instance_display_events(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[DisplayEvent, AgentTopic], Coroutine[Any, Any, None]],
        js: Optional[JetStreamContext] = None,
        ack_on_fail=True,
    ):
        subject = topic_manager.get_subject_for_all_display_events_within_agent_instance()
        queue_group = topic_manager.get_stream_group_for_all_display_events_within_agent()

        stream_name = topic_manager.get_stream_name_for_all_events_in_agent()
        stream_subject = topic_manager.get_subject_for_all_events_in_agent()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=DisplayEvent,
            handler=handler,
            js=js,
            ack_on_fail=ack_on_fail,
        )
