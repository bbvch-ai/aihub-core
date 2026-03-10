from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS

from swiss_ai_hub.core.nats.events import BaseEvent, ControlEvent, DisplayEvent
from swiss_ai_hub.core.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from swiss_ai_hub.core.nats.subscribers.NCSubscriber import NCSubscriber
from swiss_ai_hub.core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from swiss_ai_hub.core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.nats.topics import AgentInstanceTopic
from swiss_ai_hub.core.nats.topics.discovery.agent.AgentClassDiscoveryTopic import AgentClassDiscoveryTopic


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
