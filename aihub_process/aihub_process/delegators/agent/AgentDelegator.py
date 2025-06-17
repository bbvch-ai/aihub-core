import logging
from typing import Annotated, Awaitable, Callable, Type

from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import (
    AgentWorkEvent,
    AgentWorkRequestEvent,
    ControlEvent,
    ProcessStartEvent,
    WorkRequestEvent,
)
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessWalkthroughTopicManager import ProcessWalkthroughTopicManager
from aihub_lib.nats.topics import AgentTopic
from aihub_lib.nats.topics.process.ProcessTopic import ProcessTopic
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent as AgentInThread
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from bson import ObjectId
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.AbstractEntityDelegator import AbstractEntityDelegator

logger = logging.getLogger(__name__)


class AgentDelegator(AbstractEntityDelegator):
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
        super().__init__(process_class, process_id, nc, js, topic_manager, queue_group)
        self.external_agent_event_distributor = ExternalAgentEventDistributor(nc=self.nc, js=self.js)

    async def start(self):
        await super().start()

        logger.debug(f"Subscribed to agent work request event within process '{self.process_id}'")

        logger.debug(f"Starting agent delegator for process '{self.process_id}'")
        for work_event, config in self.process_class.get_events_with_agent_in():
            logger.debug(f"Found process step with agent work input: '{work_event.event_name_from_class()}'")
            stop_events = work_event.get_stop_event_type()

            for stop_event in stop_events:
                agent_instance_topic_manager = AgentInstanceTopicManager(
                    agent_class=config.agent_class,
                    agent_id=config.agent_id,
                )

                handler = self.handle_process_step_input_factory(
                    work_event_type=work_event,
                    is_process_start=issubclass(work_event, ProcessStartEvent),
                )

                subscription = AgentNCSubscriber.for_specific_control_event_in_agent_instance(
                    nc=self.nc,
                    topic_manager=agent_instance_topic_manager,
                    handler=handler,
                    event=stop_event,
                )
                await subscription.start()
                self.subscriptions.append(subscription)

                logger.debug(
                    f"Subscribed to agent '{config.agent_class}' with id '{config.agent_id}' for event '{stop_event.event_name_from_class()}'"
                )

    def handle_process_step_input_factory(
        self, work_event_type: Type[AgentWorkEvent], is_process_start: bool
    ) -> Callable[[ControlEvent, AgentTopic], Awaitable[None]]:
        async def _handle_process_step_input(
            event: Annotated[ControlEvent, "The incoming agent event to handle."],
            topic: Annotated[AgentTopic, "The parsed topic of the event."],
        ):
            logger.debug(f"Handling agent event: {event.event_name}")
            work_event = work_event_type(agent_event=event)

            # Create a new process walkthrough
            if is_process_start:
                process_walkthrough_id = str(ObjectId())
                logger.debug(f"Creating new walkthrough with ID {process_walkthrough_id}")
            else:
                thread = ThreadEntity.get_thread_by_id(topic.thread_id)
                process_walkthrough_id = thread.process_walkthrough_id
                logger.debug(f"Continuing existing walkthrough with ID {process_walkthrough_id}")

            walkthrough_topic_manager = ProcessWalkthroughTopicManager.from_process_instance_topic_manager(
                topic_manager=self.topic_manager, process_walkthrough_id=process_walkthrough_id
            )
            subject = walkthrough_topic_manager.get_subject_for_work_event_in_walkthrough(
                event_name=work_event.event_name,
                event_id=work_event.event_id,
            )
            logger.debug(f"Publishing work {work_event} to subject '{subject}'")
            await self.js_publisher.publish_event(work_event, subject)

        return _handle_process_step_input

    async def handle_process_step_output(self, event: WorkRequestEvent, topic: ProcessTopic):
        if not isinstance(event, AgentWorkRequestEvent):
            return

        logger.debug(f"Delegating agent output to external agent: {event.agent_class} with id {event.agent_id}")
        thread_id = ObjectId()
        display_id = ObjectId()

        ThreadEntity.create_process_thread(
            name=self.process_class.__name__,
            agent=AgentInThread(agent_class=event.agent_class, agent_id=event.agent_id),
            thread_id=thread_id,
            process_class=self.process_class.__name__,
            process_id=self.process_id,
            process_walkthrough_id=topic.process_walkthrough_id,
        )

        external_event = ExternalAgentEvent(
            thread_id=str(thread_id),
            display_id=str(display_id),
            event=event.start_event,
        )

        await self.external_agent_event_distributor.distribute_event(external_event=external_event)
