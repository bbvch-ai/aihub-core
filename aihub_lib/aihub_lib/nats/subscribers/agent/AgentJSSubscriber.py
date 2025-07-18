from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.nats.events import BaseEvent, ControlEvent
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topics import AgentTopic


class AgentJSSubscriber(JSSubscriber):
    @classmethod
    def for_agent_instance_control_events(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[ControlEvent, AgentTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        config_type: type[AgentConfig] = AgentConfig,
    ):
        """Subscribe to all control events within a specific agent instance."""
        subject = topic_manager.get_subject_for_all_control_events_within_agent_instance()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
            config_type=config_type,
        )

    @classmethod
    def for_agent_class_control_events(
        cls,
        nc: NATS,
        topic_manager: AgentClassTopicManager,
        handler: Callable[[ControlEvent, AgentTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        config_type: type[AgentConfig] = AgentConfig,
    ):
        """Subscribe to all control events for a specific agent class."""
        subject = topic_manager.get_subject_for_all_control_events_within_agent_class()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
            config_type=config_type,
        )

    @classmethod
    def for_agent_instance_events(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[BaseEvent, AgentTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        config_type: type[AgentConfig] = AgentConfig,
    ):
        """Subscribe to all events within a specific agent instance."""
        subject = topic_manager.get_subject_for_everything_within_agent_instance()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=ControlEvent,
            handler=handler,
            js=js,
            config_type=config_type,
        )
