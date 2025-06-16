import abc
from typing import Annotated, Type

from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

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

    @abc.abstractmethod
    async def start(self):
        pass

    @abc.abstractmethod
    async def stop(self):
        pass
