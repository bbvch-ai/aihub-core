import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Annotated, Any, override

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import Redis
from swiss_ai_hub.core.dispatcher import BaseDispatcher, EventsAndKwargs
from swiss_ai_hub.core.events.process import (
    AgentWorkRequestEvent,
    HumanWorkRequestEvent,
    ProcessEvent,
    ProcessExceptionEvent,
    ProcessStopEvent,
    ProgramWorkRequestEvent,
    WorkEvent,
)
from swiss_ai_hub.core.form import Form, transform_formkit_arrays
from swiss_ai_hub.core.processes import ProcessConfig
from swiss_ai_hub.core.rpc import ProcessConfigClient
from swiss_ai_hub.core.topic_managers import ProcessClassTopicManager, ProcessWalkthroughTopicManager
from swiss_ai_hub.core.topics import ProcessClassTopic
from swiss_ai_hub.core.topics.process import ProcessInstanceTopic

from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.context.walkthrough.walkthrough_context import WalkthroughContext
from swiss_ai_hub.process.delegators.agent.agent import Agent
from swiss_ai_hub.process.delegators.human.human import Human
from swiss_ai_hub.process.delegators.process.process import Process
from swiss_ai_hub.process.delegators.program.program import Program
from swiss_ai_hub.process.i18n.process_locale_handler import ProcessLocaleHandler

logger = logging.getLogger(__name__)


class ProcessDispatcher(BaseDispatcher):
    def __init__(
        self,
        process: Annotated[type[AgenticProcess], "The agentic process defining steps and logic."],
        process_config: Annotated[
            ProcessConfig, "Form-mode configuration with FormKit elements and non-configurable values."
        ],
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        redis: Annotated[Redis, "Redis client for distributed storage."],
        topic_manager: Annotated[ProcessClassTopicManager, "Manages event subjects for this agent class."],
        locale_handler: Annotated[ProcessLocaleHandler, "Manages localization for the agent."],
    ):
        super().__init__(nc, js, redis, topic_manager, ProcessClassTopic, dispatch_entity_name=process.__name__)
        self.process = process
        self.process_config = process_config
        self.locale_handler = locale_handler

        self.process_config_type: type[ProcessConfig] = self.process_config.__class__

        # Pre-compute non-configurable values for merging with incoming configs
        self._non_configurable_values = process_config.get_non_configurable_values()

        # Client for fetching process configuration via NATS RPC
        self._config_client = ProcessConfigClient(nc=nc)

    async def _fetch_config_from_event(self, event: WorkEvent) -> dict[str, Any]:
        """
        Fetch the process config for a start event via NATS RPC.

        Extracts the process_id from the event's process_config dict, then fetches
        the full config from the API. Falls back to the event's process_config
        if the RPC call fails.
        """
        process_class = self.process.__name__

        event_config: dict[str, Any] = getattr(event, "process_config", None) or {}
        process_id = event_config.get("process_id", "")

        if not process_id:
            logger.warning(f"No process_id in start event for {process_class}, using event config as fallback")
            return event_config

        try:
            return await self._config_client.fetch_config(
                process_class=process_class,
                process_id=process_id,
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch config via RPC for {process_class}/{process_id}: {e}. Falling back to event config."
            )
            return event_config

    @override
    async def handle_event(
        self,
        event: Annotated[WorkEvent, "The incoming work event to handle."],
        topic: Annotated[ProcessClassTopic, "The parsed topic of the event."],
    ):
        await super().handle_event(event, topic)

        walkthrough_context = WalkthroughContext(self.redis, topic.process_walkthrough_id)

        process_config_dict: dict[str, Any] | None = None
        if event.is_process_start_event:
            submitted_config = await self._fetch_config_from_event(event)

            # Deep merge: non-configurable values (from form-mode config) + configurable values (from submission)
            process_config_dict = Form.deep_merge(self._non_configurable_values, submitted_config)
            await walkthrough_context.set("_process_config", process_config_dict)

        if process_config_dict is None:
            process_config_dict = await walkthrough_context.get("_process_config")
            if process_config_dict is None:
                raise ValueError(f"No process config found for event {event.event_name} and topic {topic}")

        # Transform FormKit-style arrays (dict with numeric keys) to Python lists
        process_config_dict = transform_formkit_arrays(process_config_dict)
        walkthrough_process_config = self.process_config_type.model_validate(process_config_dict)
        topic = ProcessInstanceTopic.from_process_class_topic(
            process_class_topic=topic,
            process_id=walkthrough_process_config.process_id,
        )

        if event.is_process_start_event:
            logger.debug(f"Handling ProcessStartEvent: {event.event_name}")

        if event.is_process_stop_event:
            logger.debug(f"Handling ProcessStopEvent: {event.event_name}")
            await walkthrough_context.delete_all()
            await self.event_store.delete_all(topic.execution_context_id)
            await self.step_store.delete_all(topic.execution_context_id)
            return

        if event.is_process_exception_event:
            logger.debug(f"Handling ProcessExceptionEvent: {event.event_name}")
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
                task = asyncio.create_task(
                    self.execute_step(event, step_method, events, topic, walkthrough_process_config)
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

    @override
    async def is_step_ready(
        self,
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[dict[str, list[WorkEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[ProcessInstanceTopic, "Topic info for the current process."],
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
        topic: Annotated[ProcessInstanceTopic, "Topic info for the current process."],
        process_config: Annotated[ProcessConfig, "Configuration for the process."],
    ):
        events_and_kwargs: EventsAndKwargs = await self._build_method_kwargs(
            trigger_event,
            step_method,
            events,
            process_config,
        )

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
                    event.user_ids = config.user_ids
                    event.user_emails = config.user_emails
                    event.user_roles = config.user_roles
                    event.notify = config.notify

                elif isinstance(event, ProcessStopEvent) and isinstance(config, Process.Out):
                    logger.debug("Step return correctly identified as ProcessStopEvent")
                    event.process_class = topic.process_class
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
        event: Annotated[ProcessEvent, "The event to publish."],
        topic: Annotated[ProcessInstanceTopic, "Current process topic context."],
    ):
        """
        Publishes a given event to the correct subject.
        Uses the per-walkthrough topic manager to form the right event subject and publishes via JSPublish.
        """
        topic_manager = self.get_topic_manager_for_process_walkthrough(topic)

        if event.is_work_request_event:
            subject = topic_manager.get_subject_for_work_request_event_in_walkthrough(event.event_name, event.event_id)
            event.process_id = topic.process_id
            await self.js_publisher.publish_event(event, subject)

        if event.is_work_event:
            subject = topic_manager.get_subject_for_work_event_in_walkthrough(event.event_name, event.event_id)
            await self.js_publisher.publish_event(event, subject)

    async def _build_method_kwargs(
        self,
        trigger_event: Annotated[WorkEvent, "The event that triggered the step."],
        method: Annotated[Callable, "The step method to execute."],
        events: Annotated[dict[str, list[WorkEvent]], "All events for this run, keyed by event name."],
        process_config: Annotated[ProcessConfig, "Configuration for the process."],
    ) -> EventsAndKwargs:
        events_and_kwargs: EventsAndKwargs = await self._build_event_kwargs(trigger_event, method, events)

        step_signature = inspect.signature(method)
        for param in step_signature.parameters.values():
            if inspect.isclass(param.annotation) and issubclass(param.annotation, ProcessConfig):
                if param.annotation != self.process_config_type:
                    raise ValueError(
                        f"Expected ProcessConfig type '{self.process_config_type.__name__}', "
                        f"but got '{param.annotation.__name__}' for parameter '{param.name}'."
                    )
                logger.debug(
                    f"Injected dynamic configuration for parameter '{param.name}' of type '{param.annotation.__name__}'"
                )
                events_and_kwargs.kwargs[param.name] = process_config

        return events_and_kwargs

    def get_topic_manager_for_process_walkthrough(
        self, topic: Annotated[ProcessInstanceTopic, "Topic identifying the run/thread."]
    ) -> ProcessWalkthroughTopicManager:
        """
        Returns a thread-specific topic manager derived from the agent's instance topic manager.
        Useful for publishing thread-scoped events.
        """
        return ProcessWalkthroughTopicManager.from_process_class_topic_manager(
            topic_manager=self.topic_manager,
            process_walkthrough_id=topic.process_walkthrough_id,
            process_id=topic.process_id,
        )
