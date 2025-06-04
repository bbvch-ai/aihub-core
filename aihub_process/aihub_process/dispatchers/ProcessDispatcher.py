import asyncio
import logging
from typing import Annotated, Type, Callable, Dict, List

from nats.js import JetStreamContext

from aihub_lib.nats.dispatcher.BaseDispatcher import BaseDispatcher
from aihub_lib.nats.events import ControlEvent, BaseEvent
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessWalkthroughTopicManager import ProcessWalkthroughTopicManager
from aihub_lib.nats.topics.process.ProcessTopic import ProcessTopic
from aihub_process.agentic_processes.AgenticProcess import AgenticProcess

from nats.aio.client import Client as NATS
from redis.asyncio import Redis

from aihub_process.i18n.ProcessLocaleHandler import ProcessLocaleHandler


logger = logging.getLogger(__name__)


class ProcessDispatcher(BaseDispatcher):

    def __init__(
            self,
            process: Annotated[Type[AgenticProcess], "The agentic process defining steps and logic."],
            nc: Annotated[NATS, "NATS client for messaging."],
            js: Annotated[
                JetStreamContext,
                "JetStream context for persistent storage and event streams.",
            ],
            redis: Annotated[Redis, "Redis client for distributed storage."],
            topic_manager: Annotated[ProcessInstanceTopicManager, "Manages event subjects for this agent instance."],
            locale_handler: Annotated[ProcessLocaleHandler, "Manages localization for the agent."],
    ):
        super().__init__(nc, js, redis, topic_manager, ProcessTopic)
        self.process = process
        self.nc = nc
        self.js = js
        self.locale_handler = locale_handler

        # Initialization flag
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def handle_event(
        self,
        event: Annotated[ControlEvent, "The incoming control event to handle."],
        topic: Annotated[ProcessTopic, "The parsed topic of the event."],
    ):
        await super().handle_event(event, topic)

        steps = self.process.get_steps_waiting_for_event(type(event))
        for step_method in steps:
            logger.debug(f"Checking step '{step_method.__name__}' for readiness")
            input_events = getattr(step_method, "_input_events", set())
            input_event_class_names = [event_class.event_name_from_class() for event_class in input_events]
            events = await self.event_store.get_events_of_multiple_types(
                topic.execution_context_id, input_event_class_names, until_event=event
            )
            if await self.is_step_ready(step_method, events, topic):
                logger.debug(f"Triggering step '{step_method.__name__}' due to event '{event.event_name}'")
                asyncio.create_task(self.execute_step(event, step_method, events, topic))

    async def is_step_ready(
        self,
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[ProcessTopic, "Topic info for the current process."],
    ) -> bool:
        """
        Checks if a step can be run given the current state (events available, max executions, etc.).

        It verifies:
        - The run hasn't crashed.
        - The step hasn't exceeded its max execution count.
        - All required input events are available in the needed quantities.

        Returns True if the step can execute, False otherwise.
        """
        return await self.step_meets_basic_execution_requirements(step_method, events, topic)

    async def execute_step(
            self,
            trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
            step_method: Annotated[Callable, "The step method to execute."],
            events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event name."],
            topic: Annotated[ProcessTopic, "Topic info for the current process."],
    ):
        # TODO implement
        pass

    def get_topic_manager_for_process_walkthrough(
        self, topic: Annotated[ProcessTopic, "Topic identifying the run/thread."]
    ) -> ProcessWalkthroughTopicManager:
        """
        Returns a thread-specific topic manager derived from the agent's instance topic manager.
        Useful for publishing thread-scoped events.
        """
        return ProcessWalkthroughTopicManager.from_process_instance_topic_manager(
            topic_manager=self.topic_manager,
            process_walkthrough_id=topic.process_walkthrough_id,
        )

    async def publish_event(
        self,
        event: Annotated[BaseEvent, "The event to publish."],
        topic: Annotated[ProcessTopic, "Current process topic context."],
    ):
        """
        Publishes a given event (Control or Display) to the correct subject.
        Uses the per-thread topic manager to form the right event subject and publishes via JSPublisher.
        """
        topic_manager = self.get_topic_manager_for_process_walkthrough(topic)
        if event.is_control_event:
            subject = topic_manager.get_subject_for_control_event_in_walkthrough(event.event_name, event.event_id)
            await self.js_publisher.publish_event(event, subject)
        if event.is_display_event:
            subject = topic_manager.get_subject_for_display_event_in_walkthrough(event.event_name, event.event_id)
            await self.nc_publisher.publish_event(event, subject)