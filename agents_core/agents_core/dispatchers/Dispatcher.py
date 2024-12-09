import inspect
import logging
import traceback
from typing import Type, Dict, Set, List, get_origin, Callable, Any, Optional
import asyncio

from nats.js import JetStreamContext

from agents_core.agents.abstract.Agent import Agent
from agents_core.agents.abstract.AgentConfig import AgentConfig
from agents_core.displayers.EventDisplayer import EventDisplayer
from lib_core.nats.context.run.RunContext import RunContext
from lib_core.nats.context.thread.ThreadContext import ThreadContext
from lib_core.nats.events import ControlEvent, StartEvent, StopEvent, ExceptionEvent, BaseEvent, DisplayEvent
from lib_core.nats.events.human_in_the_loop import HumanInTheLoopRequestEvent
from lib_core.nats.publishers.JSPublisher import JSPublisher
from lib_core.nats.stores.event.DistributedEventStore import DistributedEventStore
from lib_core.nats.stores.step.StepStore import DistributedStepStore
from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from agents_core.tracing.coordinators.RunTraceCoordinator import RunTraceCoordinator
from agents_core.workflow.annotations.custom_types.ListOfSize import ListOfSize

logger = logging.getLogger(__name__)


class Dispatcher:
    def __init__(
        self,
        agent: Type[Agent],
        agent_config: AgentConfig,
        js: JetStreamContext,
        topic_manager: AgentInstanceTopicManager,
    ):
        self.agent = agent
        self.agent_config = agent_config
        self.js = js
        self.topic_manager = topic_manager
        self.publisher = JSPublisher(self.js)
        self.event_store = DistributedEventStore(js)
        self.step_store = DistributedStepStore(js)
        self.tracer = RunTraceCoordinator()
        self.step_configs = agent_config.get_step_configs()

    async def handle_event(self, event: ControlEvent, topic: AgentTopic):
        logger.debug(f"Handling event for subject {topic}")
        # Store the event
        await self.event_store.store_event(topic.run_id, event)

        # Retrieve contexts
        run_context = await RunContext.create(self.js, topic.thread_id, topic.run_id)
        thread_context = await ThreadContext.create(self.js, topic.thread_id)

        if isinstance(event, StartEvent):
            telemetry_headers = self.tracer.trace_run_start(topic, event)
            await run_context.set("telemetry_headers", telemetry_headers)

            logger.debug("Handling StartEvent")
            event_data = event.to_context_dict()
            for key, value in event_data.items():
                logger.debug(f"Setting key '{key}' to '{value}'")
                await run_context.set(key, value)

        if isinstance(event, StopEvent):
            logger.debug("Handling StopEvent")
            await run_context.delete_all()
            await self.event_store.delete_run_store(topic.run_id)
            await self.step_store.delete_run_store(topic.run_id)
            return

        if isinstance(event, ExceptionEvent):
            await self.step_store.mark_run_as_crashed(topic.run_id)
            return

        # Check for steps that are ready to execute
        steps = self.agent.get_steps_waiting_for_event(type(event))
        tasks = []
        for step_method in steps:
            logger.debug(f"Checking step '{step_method.__name__}'")
            if await self.is_step_ready(step_method, topic.run_id, event):
                logger.debug(
                    f"Triggering step '{step_method.__name__}' due to '{event.__class__.__name__}'")
                task = asyncio.create_task(
                    self.execute_step(event, step_method, run_context, thread_context, topic)
                )
                tasks.append(task)
        if tasks:
            await asyncio.gather(*tasks)

    async def is_step_ready(self, step_method: Callable, run_id: str, event: ControlEvent) -> bool:
        """Determines if a step is ready to execute based on available events."""
        if await self.step_store.is_run_crashed(run_id):
            logger.warning(f"Run {run_id} is marked as crashed, skipping step execution.")
            return False

        max_executions = getattr(step_method, '_max_executions_per_run', None)
        if max_executions is not None:
            execution_count = await self.step_store.get_execution_count(run_id, step_method.__name__)
            if execution_count >= max_executions:
                logger.debug(
                    f"[{step_method.__name__}] Max executions reached ({execution_count}/{max_executions}), skipping.")
                return False

        input_event_mapping: Dict[str, Set[Type[ControlEvent]]] = step_method._input_event_mapping
        parameter_optional_map: Dict[str, bool] = getattr(step_method, '_parameter_optional_map', {})
        size_requirements: Dict[str, Optional[int]] = getattr(step_method, '_size_requirements', {})
        events = await self.event_store.get_all_events(run_id, before=event.created_at)

        logger.debug(f"[{step_method.__name__}] Event map for {input_event_mapping}")
        for argument_name, event_types in input_event_mapping.items():
            logger.debug(f"[{step_method.__name__}] Step requires argument {argument_name}: {event_types}")
            logger.debug(f"[{step_method.__name__}] Got events: {events}")

            # Get the required size for this parameter (if any)
            required_size = size_requirements.get(argument_name)
            is_optional = parameter_optional_map.get(argument_name, False)

            # Count available events of the required types
            available_events_count = sum(
                len(events.get(event_type.__name__, []))
                for event_type in event_types
            )

            # Check if we have enough events
            if required_size is not None:
                if available_events_count < required_size:
                    logger.debug(
                        f"[{step_method.__name__}] Insufficient events for '{argument_name}'. "
                        f"Need {required_size}, have {available_events_count}")
                    return False
            elif not available_events_count and not is_optional:
                logger.debug(
                    f"[{step_method.__name__}] Insufficient inputs due to missing required argument '{argument_name}'")
                return False
            elif not available_events_count and is_optional:
                logger.debug(
                    f"[{step_method.__name__}] Optional argument '{argument_name}' missing, but proceeding")
                continue

        logger.debug(f"[{step_method.__name__}] Sufficient Inputs")
        return True

    async def _get_event_value(
        self,
        param: inspect.Parameter,
        step_method: Callable,
        events: Dict[str, List[ControlEvent]],
        trigger_event: ControlEvent,
    ) -> Optional[Any]:
        """Retrieves the appropriate event value for a given parameter."""
        event_types = step_method._input_event_mapping.get(param.name, set())
        size_requirements = getattr(step_method, '_size_requirements', {})
        required_size = size_requirements.get(param.name)

        # Get all available events of the required types
        all_matching_events: List[ControlEvent] = []
        for event_type in event_types:
            event_list = events.get(event_type.__name__, [])
            all_matching_events.extend(event_list)

        if not all_matching_events:
            return None

        # Sort events by creation time to ensure consistent ordering
        all_matching_events.sort(key=lambda x: x.created_at)

        # Handle ListOfSize
        if required_size is not None:
            if len(all_matching_events) == required_size:
                return ListOfSize(all_matching_events[-required_size:], required_size)
            return None

        # Handle regular List
        elif get_origin(param.annotation) in (list, List):
            return all_matching_events

        # Handle single event
        else:
            if trigger_event.event_id in [event.event_id for event in all_matching_events]:
                return trigger_event
            return all_matching_events[-1]  # Return the latest event

    async def execute_step(
        self,
        trigger_event: ControlEvent,
        step_method: Callable,
        run_context: RunContext,
        thread_context: ThreadContext,
        topic: AgentTopic,
    ):
        """Executes a step method with the appropriate arguments."""
        # Immediately mark run to ensure no other servers will start an execution for the same step
        await self.step_store.increment_execution_count(topic.run_id, step_method.__name__)

        kwargs: Dict[str, Any] = {}
        step_signature = inspect.signature(step_method)
        events = await self.event_store.get_all_events(topic.run_id)

        parameter_optional_map = getattr(step_method, '_parameter_optional_map', {})

        for param in step_signature.parameters.values():
            if param.name == 'self':
                continue

            if self.step_configs.get(param.annotation):
                kwargs[param.name] = self.step_configs[param.annotation]
                continue

            if issubclass(param.annotation, AgentConfig):
                kwargs[param.name] = self.agent_config
                continue

            if param.annotation == RunContext:
                kwargs[param.name] = run_context
                continue

            if param.annotation == ThreadContext:
                kwargs[param.name] = thread_context
                continue

            if param.annotation == EventDisplayer:
                kwargs[param.name] = EventDisplayer(self.publisher, topic_manager=self.get_topic_manager_for_thread(topic))
                continue

            # Handle event parameters
            event_value = await self._get_event_value(param, step_method, events, trigger_event)
            if event_value is not None or parameter_optional_map.get(param.name, False):
                kwargs[param.name] = event_value
            else:
                raise ValueError(
                    f"[{step_method.__name__}] Unable to find available event for required parameter "
                    f"'{param.name}' in step '{step_method.__name__}'"
                )

        # Instantiate the agent and execute the step method
        agent_instance = self.agent()
        telemetry_headers = await run_context.get("telemetry_headers")
        async with self.tracer.trace_step_start(telemetry_headers, topic, step_method, kwargs) as step_span:
            try:
                result = await step_method(agent_instance, **kwargs)
            except Exception as e:
                await self.tracer.trace_step_error(step_span, e)
                if getattr(step_method, '_stop_on_error', False):
                    event = ExceptionEvent(message=str(e))
                    await self.publish_event(event, topic)
                logger.error(f"Error executing step '{step_method.__name__}': {e}")
                traceback.print_exc()
                return

            # Handle output events
            if result:
                if not isinstance(result, list):
                    result = [result]
                for event in result:
                    if isinstance(event, HumanInTheLoopRequestEvent):
                        event.topic = AgentTopic.from_partial_topic(
                            partial_topic=event.topic,
                            agent_class=topic.agent_class,
                            agent_id=topic.agent_id,
                            run_id=topic.run_id,
                            thread_id=topic.thread_id,
                            display_id=topic.display_id,
                            event_id=event.event_id,
                        )

                    await self.event_store.store_event(topic.run_id, event)
                    await self.publish_event(event, topic)

            await self.tracer.trace_step_stop(step_span, result)

    def get_topic_manager_for_thread(self, topic: AgentTopic) -> AgentThreadTopicManager:
        return AgentThreadTopicManager.from_agent_instance_topic_manager(
            topic_manager=self.topic_manager,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )

    async def publish_event(self, event: BaseEvent, topic: AgentTopic):
        """Publishes a control event to the appropriate subject."""
        topic_manager = self.get_topic_manager_for_thread(topic)
        if isinstance(event, ControlEvent):
            subject = topic_manager.get_subject_for_control_event_in_thread(event.__class__.__name__, event.event_id)
            await self.publisher.publish_event(event, subject)
        if isinstance(event, DisplayEvent):
            subject = topic_manager.get_subject_for_display_event_in_thread(event.__class__.__name__, event.event_id)
            await self.publisher.publish_event(event, subject)
