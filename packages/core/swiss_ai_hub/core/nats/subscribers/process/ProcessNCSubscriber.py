from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS

from swiss_ai_hub.core.nats.events.BaseEvent import BaseEvent
from swiss_ai_hub.core.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from swiss_ai_hub.core.nats.events.process.ProcessEvent import ProcessEvent
from swiss_ai_hub.core.nats.subscribers.NCSubscriber import NCSubscriber
from swiss_ai_hub.core.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from swiss_ai_hub.core.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from swiss_ai_hub.core.nats.topics.discovery.process.ProcessClassDiscoveryTopic import ProcessClassDiscoveryTopic
from swiss_ai_hub.core.nats.topics.process.ProcessInstanceTopic import ProcessInstanceTopic


class ProcessNCSubscriber(NCSubscriber[BaseEvent]):
    @classmethod
    def for_process_class_discovery_request_events(
        cls,
        nc: NATS,
        topic_manager: ProcessTopicManager,
        handler: Callable[[ClassDiscoveryRequestEvent, ProcessClassDiscoveryTopic], Awaitable[None]],
        call_id: str = "*",
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to discovery request events for all processes"""
        subject = topic_manager.get_process_class_discovery_subject_request(call_id)
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=ClassDiscoveryRequestEvent,
            handler=handler,
        )

    @classmethod
    def for_process_class_discovery_response_events(
        cls,
        nc: NATS,
        topic_manager: ProcessTopicManager,
        handler: Callable[[BaseEvent, ProcessClassDiscoveryTopic], Awaitable[None]],
        call_id: str = "*",
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to discovery response events for processes, optionally filtered by a specific call_id."""
        subject = topic_manager.get_process_class_discovery_subject_response(call_id)
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_all_process_events(
        cls,
        nc: NATS,
        topic_manager: ProcessTopicManager,
        handler: Callable[[ProcessEvent, ProcessInstanceTopic], Awaitable[None]],
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all events within a specific process"""
        subject = topic_manager.get_subject_for_all_events_in_process()
        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            handler=handler,
            event_cls=ProcessEvent,
        )

    @classmethod
    def for_specific_work_event_in_process_instance(
        cls,
        nc: NATS,
        topic_manager: ProcessInstanceTopicManager,
        handler: Callable[[BaseEvent, ProcessInstanceTopic], Awaitable[None]],
        event: type[BaseEvent],
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all events within a specific process instance"""
        subject = topic_manager.get_subject_for_specific_event_in_process_instance(
            process_walkthrough_id="*",
            event_type=ProcessTopicManager.WORK_EVENT,
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
