import abc
from typing import Annotated, Type

from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topics.process.ProcessTopic import ProcessTopic
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess


class AbstractEntityDelegator(abc.ABC):
    def _init__(
        self,
        process: Annotated[Type[AgenticProcess], "The agentic process defining steps and logic."],
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        topic_manager: Annotated[ProcessInstanceTopicManager, "Manages event subjects."],
        topic: Annotated[Type[ProcessTopic], "Topic under which these events were published"],
    ):
        self.process = process
        self.nc = nc
        self.js = js

        self.js_publisher = JSPublisher(self.js)

        self.topic_manager = topic_manager
        self.topic = topic

    @abc.abstractmethod
    async def start(self):
        pass

    @abc.abstractmethod
    async def stop(self):
        pass
