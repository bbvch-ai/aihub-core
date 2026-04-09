from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.events.discovery.class_discovery_request_event import ClassDiscoveryRequestEvent
from swiss_ai_hub.core.subscribers.nc_subscriber import NCSubscriber
from swiss_ai_hub.core.topic_managers.agents.agent_instance_topic_manager import AgentInstanceTopicManager
from swiss_ai_hub.core.topic_managers.agents.agent_thread_topic_manager import AgentThreadTopicManager
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic
from swiss_ai_hub.core.topics.discovery.agent.agent_class_discovery_topic import AgentClassDiscoveryTopic


class AgentNCSubscriber(NCSubscriber[BaseEvent]):
    @classmethod
    def for_all_agents_display_events(
        cls,
        nc: NATS,
        topic_manager: AgentTopicManager,
        handler: Callable[[DisplayEvent, AgentInstanceTopic], Awaitable[None]],
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all display events from all agents."""
        subject = topic_manager.get_subject_for_all_display_events_in_agent()
        return cls(
            name=subscriber_name,
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
        handler: Callable[[DisplayEvent, AgentInstanceTopic], Awaitable[None]],
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all display events within a specific thread."""
        subject = topic_manager.get_subject_for_display_event_in_thread("*", "*")
        return cls(
            name=subscriber_name,
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
        handler: Callable[[ControlEvent, AgentInstanceTopic], Awaitable[None]],
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all events (display, control, etc.) within a specific thread."""
        subject = topic_manager.get_subject_for_all_event_in_thread("*", "*")
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_thread_control_events(
        cls,
        nc: NATS,
        topic_manager: AgentThreadTopicManager,
        handler: Callable[[ControlEvent, AgentInstanceTopic], Awaitable[None]],
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to control events only within a specific thread.

        Unlike for_all_thread_events, this avoids duplicate delivery for ControlAndDisplayEvent
        types (e.g. StopEvent) which are published on both control and display subjects.
        """
        subject = topic_manager.get_subject_for_control_event_in_thread("*", "*")
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=ControlEvent,
            handler=handler,
        )

    @classmethod
    def for_agent_class_discovery_request_events(
        cls,
        nc: NATS,
        topic_manager: AgentTopicManager,
        handler: Callable[[ClassDiscoveryRequestEvent, AgentClassDiscoveryTopic], Awaitable[None]],
        call_id: str = "*",
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to discovery request events for agent classes, optionally filtered by a specific call_id."""
        subject = topic_manager.get_agent_class_discovery_subject_request(call_id)
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=ClassDiscoveryRequestEvent,
            handler=handler,
        )

    @classmethod
    def for_agent_class_discovery_response_events(
        cls,
        nc: NATS,
        topic_manager: AgentTopicManager,
        handler: Callable[[BaseEvent, AgentInstanceTopic], Awaitable[None]],
        call_id: str = "*",
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to discovery response events for agent classes, optionally filtered by a specific call_id."""
        subject = topic_manager.get_agent_class_discovery_subject_response(call_id)
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_all_agent_events(
        cls,
        nc: NATS,
        topic_manager: AgentTopicManager,
        handler: Callable[[BaseEvent, AgentInstanceTopic], Awaitable[None]],
        subscriber_name: str = "Unnamed",
    ):
        """
        Creates a NCSubscriber for all agent events.
        Use this when you want a single subscriber to handle every agent event in the system.
        """
        subject = topic_manager.get_subject_for_all_events_in_agent()

        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_specific_control_event_in_agent_instance(
        cls,
        nc: NATS,
        topic_manager: AgentInstanceTopicManager,
        handler: Callable[[ControlEvent, AgentInstanceTopic], Awaitable[None]],
        event: type[ControlEvent],
        subscriber_name: str = "Unnamed",
    ):
        """
        Creates a NCSubscriber for all agent events.
        Use this when you want a single subscriber to handle every agent event in the system.
        """
        subject = topic_manager.get_subject_for_specific_event_in_agent_instance(
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=AgentTopicManager.CONTROL_EVENT,
            event_name=event.event_name_from_class(),
            event_id="*",
        )

        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )
