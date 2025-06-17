import abc
from typing import Annotated, Type, List, Callable, Coroutine, Any, Awaitable

from aihub_lib.nats.events import WorkRequestEvent, WorkEvent, BaseEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.subscribers.process.ProcessJSSubscriber import ProcessJSSubscriber
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from aihub_lib.nats.topics import ProcessTopic, Topic
from aihub_process.agentic_processes.AgenticProcess import AgenticProcess


class AbstractEntityDelegator(abc.ABC):
    def __init__(
        self,
        process_class: Annotated[Type[AgenticProcess], "The agentic process defining steps and logic."],
        process_id: Annotated[str, "Process ID"],
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        topic_manager: Annotated[ProcessInstanceTopicManager, "Manages event subjects."],
        queue_group: str,
    ):
        self.process_class = process_class
        self.process_id = process_id
        self.nc = nc
        self.js = js

        self.js_publisher = JSPublisher(self.js)

        self.topic_manager = topic_manager

        self.queue_group = queue_group

        self.subscriptions: List[ProcessNCSubscriber | ProcessJSSubscriber] = []

    async def start(self):
        subscription = ProcessJSSubscriber.for_process_instance_work_request_events(
            nc=self.nc,
            topic_manager=self.topic_manager,
            handler=self.handle_process_step_output,
            queue_group=self.queue_group,
            js=self.js,
        )
        await subscription.start()
        self.subscriptions.append(subscription)

    async def stop(self):
        for subscription in self.subscriptions:
            await subscription.stop()

    @abc.abstractmethod
    def handle_process_step_input_factory(self, work_event_type: Type[WorkEvent], is_process_start: bool) -> Callable[[BaseEvent, Topic], Awaitable[None]]:
        pass

    @abc.abstractmethod
    async def handle_process_step_output(self, event: WorkRequestEvent, topic: ProcessTopic):
        pass