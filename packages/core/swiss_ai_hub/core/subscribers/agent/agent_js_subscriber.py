from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.subscribers.js_subscriber import JSSubscriber
from swiss_ai_hub.core.topic_managers.agents.agent_class_topic_manager import AgentClassTopicManager
from swiss_ai_hub.core.topic_managers.agents.agent_instance_topic_manager import AgentInstanceTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic


class AgentJSSubscriber(JSSubscriber[BaseEvent]):
    @classmethod
    def for_agent_instance_control_events(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[ControlEvent, AgentInstanceTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all control events within a specific agent instance."""
        subject = topic_manager.get_subject_for_all_control_events_within_agent_instance()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
        )

    @classmethod
    def for_agent_class_control_events(
        cls,
        nc: NATS,
        topic_manager: AgentClassTopicManager,
        handler: Callable[[ControlEvent, AgentInstanceTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all control events for a specific agent class."""
        subject = topic_manager.get_subject_for_all_control_events_within_agent_class()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
        )
