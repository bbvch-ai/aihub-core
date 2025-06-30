from typing import Awaitable, Callable, Type

from nats.aio.client import Client as NATS

from aihub_lib.nats.events import BaseEvent, DiscoveryRequestEvent, ProcessEvent
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics.process.ProcessTopic import ProcessTopic


class ProcessNCSubscriber(NCSubscriber):
    @classmethod
    def for_process_discovery_request_events(
        cls,
        nc: NATS,
        topic_manager: ProcessTopicManager,
        handler: Callable[[DiscoveryRequestEvent, ProcessTopic], Awaitable[None]],
        call_id: str = "*",
    ):
        subject = topic_manager.get_process_discovery_subject_request(call_id)
        return cls(
            nc=nc,
            subject=subject,
            event_cls=DiscoveryRequestEvent,
            handler=handler,
        )

    @classmethod
    def for_all_process_events(
        cls,
        nc: NATS,
        topic_manager: ProcessTopicManager,
        handler: Callable[[ProcessEvent, ProcessTopic], Awaitable[None]],
    ):
        subject = topic_manager.get_subject_for_all_events_in_process()
        return cls(
            nc=nc,
            subject=subject,
            handler=handler,
            event_cls=ProcessEvent,
        )

    @classmethod
    def for_specific_work_request_event_in_process_instance(
        cls,
        nc: NATS,
        topic_manager: ProcessInstanceTopicManager,
        handler: Callable[[BaseEvent, ProcessTopic], Awaitable[None]],
        event: Type[BaseEvent],
    ):
        subject = topic_manager.get_subject_for_specific_event_in_process_instance(
            process_walkthrough_id="*",
            event_type=ProcessTopicManager.WORK_REQUEST_EVENT,
            event_name=event.event_name_from_class(),
            event_id="*",
        )

        return cls(
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )
