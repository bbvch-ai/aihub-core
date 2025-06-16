import asyncio
import logging
from typing import Annotated, Callable, Dict, List, Type

from aihub_lib.nats.dispatcher.BaseDispatcher import BaseDispatcher
from aihub_lib.nats.events import (
    AgentWorkRequestEvent,
    BaseEvent,
    HumanWorkRequestEvent,
    ProcessExceptionEvent,
    ProcessStopEvent,
    ProgramWorkRequestEvent,
    WorkEvent,
)
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessWalkthroughTopicManager import ProcessWalkthroughTopicManager
from aihub_lib.nats.topics.process.ProcessTopic import ProcessTopic
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.human.Human import Human
from aihub_process.delegators.process.Process import Process
from aihub_process.delegators.program.Program import Program
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
        event: Annotated[WorkEvent, "The incoming work event to handle."],
        topic: Annotated[ProcessTopic, "The parsed topic of the event."],
    ):
        await super().handle_event(event, topic)

        if event.is_process_start_event:
            logger.debug(f"Handling ProcessStartEvent: {event.event_name}")

        if event.is_process_stop_event:
            logger.debug(f"Handling ProcessStopEvent: {event.event_name}")
            await self.event_store.delete_all(topic.execution_context_id)
            await self.step_store.delete_all(topic.execution_context_id)

        if event.is_process_exception_event:
            logger.debug(f"Handling ProcessExceptionEvent: {event.event_name}")
            # Mark run as crashed so no further steps are executed
            await self.step_store.mark_execution_context_as_crashed(topic.execution_context_id)
            return

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
        events: Annotated[Dict[str, List[WorkEvent]], "All events for this run, keyed by event name."],
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
        trigger_event: Annotated[WorkEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to execute."],
        events: Annotated[Dict[str, List[WorkEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[ProcessTopic, "Topic info for the current process."],
    ):
        all_input_events, kwargs = await self._build_event_kwargs(trigger_event, step_method, events)

        duplicated_run = await self.step_store.was_called_with_events(
            topic.execution_context_id, step_method.__name__, all_input_events
        )
        if duplicated_run:
            logger.debug(f"Skipping step '{step_method.__name__}' as it has already been called with the same events.")
            return

        await self.step_store.report_execution_context_with_events(
            topic.execution_context_id, step_method.__name__, all_input_events
        )

        process_instance = self.process()

        try:
            result = await step_method(process_instance, **kwargs)
        except Exception as e:
            event = ProcessExceptionEvent(message=str(e))
            await self.publish_event(event, topic)
            logger.exception(e)
            logger.exception(f"Error executing step '{step_method.__name__}': {e}")
            return

        if result:
            if not isinstance(result, list):
                result = [result]

            event_type_config_tuples = getattr(step_method, "_process_outputs", [])
            event_types, configs = zip(*event_type_config_tuples)

            if len(event_types) != len(result):
                raise RuntimeError(
                    f"Step '{step_method.__name__}' returned {len(result)} events, but expected {len(event_types)}"
                )

            for event, event_type, config in zip(result, event_types, configs):
                if not isinstance(event, event_type):
                    raise RuntimeError(
                        f"Step '{step_method.__name__}' returned an event of type {type(event)}, but expected {event_type}"
                    )

                if isinstance(event, AgentWorkRequestEvent) and isinstance(config, Agent.Out):
                    event.agent_class = config.agent_class
                    event.agent_id = config.agent_id

                elif isinstance(event, ProgramWorkRequestEvent) and isinstance(config, Program.Out):
                    event.endpoint = config.endpoint
                    event.method = config.method

                elif isinstance(event, HumanWorkRequestEvent) and isinstance(config, Human.Out):
                    event.users = config.users

                elif isinstance(event, ProcessStopEvent) and isinstance(config, Process.Out):
                    event.process_class = topic.process_class
                    event.process_id = topic.process_id
                    event.process_walkthrough_id = topic.process_walkthrough_id
                    print("Received process STOP event")

                else:
                    raise RuntimeError(
                        f"Mismatch found between event '{event.__class__.__name__}' and config '{config.__class__.__name__}' step '{step_method.__name__}'"
                    )

                await self.publish_event(event, topic)

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
        Publishes a given event to the correct subject.
        Uses the per-thread topic manager to form the right event subject and publishes via JSPublisher.
        """
        topic_manager = self.get_topic_manager_for_process_walkthrough(topic)
        subject = topic_manager.get_subject_for_work_request_event_in_walkthrough(event.event_name, event.event_id)

        if not (event.is_work_request_event or event.is_process_exception_event or event.is_process_stop_event):
            raise ValueError("ProcessDispatcher must only emit WorkRequest-, ProcessException-, or ProcessStop-Events")

        logger.debug(f"Publishing event '{event.event_name}' to subject '{subject}'")
        await self.js_publisher.publish_event(event, subject)
