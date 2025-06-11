from typing import Awaitable, Callable

from nats.aio.client import Client as NATS

from aihub_lib.nats.events import DiscoveryRequestEvent
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
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
