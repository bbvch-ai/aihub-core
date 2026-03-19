from collections.abc import Awaitable, Callable

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.events.process.work.work_event import WorkEvent
from swiss_ai_hub.core.events.process.work_request.work_request_event import WorkRequestEvent
from swiss_ai_hub.core.subscribers.js_subscriber import JSSubscriber
from swiss_ai_hub.core.topic_managers.process.process_class_topic_manager import ProcessClassTopicManager
from swiss_ai_hub.core.topic_managers.process.process_instance_topic_manager import ProcessInstanceTopicManager
from swiss_ai_hub.core.topics.process.process_class_topic import ProcessClassTopic
from swiss_ai_hub.core.topics.process.process_instance_topic import ProcessInstanceTopic


class ProcessJSSubscriber(JSSubscriber[BaseEvent]):
    @classmethod
    def for_process_class_work_events(
        cls,
        nc: NATS,
        topic_manager: ProcessClassTopicManager,
        handler: Callable[[WorkEvent, ProcessClassTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all work events within a specific process class."""
        subject = topic_manager.get_subject_for_all_work_events_within_process_class()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=WorkEvent,
            handler=handler,
            js=js,
        )

    @classmethod
    def for_process_class_work_request_events(
        cls,
        nc: NATS,
        topic_manager: ProcessClassTopicManager,
        handler: Callable[[WorkRequestEvent, ProcessClassTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all work request events within a specific process class."""
        subject = topic_manager.get_subject_for_all_work_request_events_within_process_class()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=WorkRequestEvent,
            handler=handler,
            js=js,
        )

    @classmethod
    def for_process_instance_work_events(
        cls,
        nc: NATS,
        topic_manager: ProcessInstanceTopicManager,
        handler: Callable[[BaseEvent, ProcessInstanceTopic], Awaitable[None]],
        queue_group: str,
        js: JetStreamContext | None = None,
        subscriber_name: str = "Unnamed",
    ):
        """Subscribe to all events within a specific process instance."""
        subject = topic_manager.get_subject_for_all_work_events_within_process_instance()
        stream_name, stream_subject = topic_manager.get_stream()

        return cls(
            name=subscriber_name,
            nc=nc,
            subject=subject,
            stream_subject=stream_subject,
            stream_name=stream_name,
            queue_group=queue_group,
            event_cls=WorkEvent,
            handler=handler,
            js=js,
        )
