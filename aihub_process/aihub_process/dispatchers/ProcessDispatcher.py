import asyncio
import logging
from collections.abc import Callable
from typing import Annotated

from aihub_lib.nats.dispatcher.BaseDispatcher import BaseDispatcher, EventsAndKwargs
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
from typing_extensions import override

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
        process: Annotated[type[AgenticProcess], "The agentic process defining steps and logic."],
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

    @override
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
            input_events = getattr(step_method, AgenticProcess.INPUT_EVENTS_ANNOTATION, set())
            input_event_class_names = [event_class.event_name_from_class() for event_class in input_events]
            events = await self.event_store.get_events_of_multiple_types(
                topic.execution_context_id, input_event_class_names, until_event=event
            )
            if await self.is_step_ready(step_method, events, topic):
                logger.debug(f"Triggering step '{step_method.__name__}' due to event '{event.event_name}'")
                asyncio.create_task(self.execute_step(event, step_method, events, topic))

    @override
    async def is_step_ready(
        self,
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[dict[str, list[WorkEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[ProcessTopic, "Topic info for the current process."],
    ) -> bool:
        """
        Checks if a step can be run given the current state (events available, max executions, etc.).

        It verifies:
        - The run hasn't crashed.
        - All required input events are available in the needed quantities.

        Returns True if the step can execute, False otherwise.
        """
        return await self._step_meets_basic_execution_requirements(step_method, events, topic)

    @override
    async def execute_step(
        self,
        trigger_event: Annotated[WorkEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to execute."],
        events: Annotated[dict[str, list[WorkEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[ProcessTopic, "Topic info for the current process."],
    ):
        events_and_kwargs: EventsAndKwargs = await self._build_event_kwargs(trigger_event, step_method, events)

        duplicated_run = await self.step_store.was_called_with_events(
            topic.execution_context_id, step_name=step_method.__name__, events=events_and_kwargs.events
        )
        if duplicated_run:
            logger.debug(f"Skipping step '{step_method.__name__}' as it has already been called with the same events.")
            return

        await self.step_store.report_execution_context_with_events(
            topic.execution_context_id, step_method.__name__, events_and_kwargs.events
        )

        process_instance = self.process()

        try:
            result = await step_method(process_instance, **events_and_kwargs.kwargs)
        except Exception as e:
            event = ProcessExceptionEvent(message=str(e))
            await self.publish_event(event, topic)
            logger.exception(e)
            logger.exception(f"Error executing step '{step_method.__name__}': {e}")
            return

        if result:
            if not isinstance(result, list | tuple):
                result = [result]
            result = tuple(result)

            event_type_config_tuples = getattr(step_method, AgenticProcess.PROCESS_OUTPUTS_ANNOTATION, [])
            event_types, configs = zip(*event_type_config_tuples)

            if len(event_types) != len(result):
                raise RuntimeError(
                    f"Step '{step_method.__name__}' returned {len(result)} events, but expected {len(event_types)}"
                )

            for event, event_type, config in zip(result, event_types, configs):
                logger.debug(
                    f"Process step returned '{event.event_name_from_class()}' "
                    f"and config '{config.__class__.__name__}' step '{step_method.__name__}'"
                )

                if not isinstance(event, event_type):
                    raise RuntimeError(
                        f"Step '{step_method.__name__}' returned an event of "
                        f"type {type(event)}, but expected {event_type}"
                    )

                if isinstance(event, AgentWorkRequestEvent) and isinstance(config, Agent.Out):
                    logger.debug("Step return correctly identified as AgentWorkRequestEvent")
                    event.agent_class = config.agent_class
                    event.agent_id = config.agent_id

                elif isinstance(event, ProgramWorkRequestEvent) and isinstance(config, Program.Out):
                    logger.debug("Step return correctly identified as ProgramWorkRequestEvent")
                    event.endpoint = config.endpoint
                    event.method = config.method

                elif isinstance(event, HumanWorkRequestEvent) and isinstance(config, Human.Out):
                    logger.debug("Step return correctly identified as HumanWorkRequestEvent")
                    event.users = config.users

                elif isinstance(event, ProcessStopEvent) and isinstance(config, Process.Out):
                    logger.debug("Step return correctly identified as ProcessStopEvent")
                    event.process_class = topic.process_class
                    event.process_id = topic.process_id
                    event.process_walkthrough_id = topic.process_walkthrough_id
                    logger.debug("Received process STOP event")

                else:
                    raise RuntimeError(
                        f"Mismatch found between event '{event.event_name_from_class()}' and "
                        f"config '{config.__class__.__name__}' step '{step_method.__name__}'"
                    )

                await self.publish_event(event, topic)

    @override
    async def publish_event(
        self,
        event: Annotated[BaseEvent, "The event to publish."],
        topic: Annotated[ProcessTopic, "Current process topic context."],
    ):
        """
        Publishes a given event to the correct subject.
        Uses the per-walkthrough topic manager to form the right event subject and publishes via JSPublish.
        """
        topic_manager = self.get_topic_manager_for_process_walkthrough(topic)
        subject = topic_manager.get_subject_for_work_request_event_in_walkthrough(event.event_name, event.event_id)

        if not (event.is_work_request_event or event.is_process_exception_event or event.is_process_stop_event):
            raise ValueError("ProcessDispatcher must only emit WorkRequest-, ProcessException-, or ProcessStop-Events")

        logger.debug(f"Publishing event '{event.event_name}' to subject '{subject}'")
        await self.js_publisher.publish_event(event, subject)

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
