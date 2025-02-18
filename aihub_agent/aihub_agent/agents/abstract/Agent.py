import abc
import inspect
from typing import Set, Type

from aihub_lib.nats.events.control import ControlEvent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent


class Agent(abc.ABC):
    """
    Base class for agents that execute workflow steps in response to events.

    ### Why This Class?
    An `Agent` defines a collection of steps—annotated functions—that process certain events.
    These steps form a workflow: when an event arrives, the dispatcher checks which steps can
    fire based on their declared input events. By centralizing step inspection and event-to-step
    mapping, the `Agent` class provides a consistent interface for discovery and orchestration.

    ### Key Features
    - **Step Discovery:**
      Steps are functions decorated with `@step`. The agent inspects its class members to find these
      methods, enabling automated wiring of events to step invocations.
    - **Event Mapping:**
      Each step declares which events it consumes. The agent can then quickly identify which steps
      should run when a given event type arrives.
    - **Start Events:**
      A subset of input events may be start events (subclasses of `StartEvent`), indicating how a run
      or workflow can be initiated.

    ### Typical Workflow
    1. The agent defines multiple step methods using `@step`, each expecting certain event types.
    2. When a `ControlEvent` arrives, the dispatcher queries `get_steps_waiting_for_event` to find
       all steps that can trigger from that event.
    3. The dispatcher then executes these steps, passing in the required events and contexts.

    ### Example
    Suppose an agent has `my_step` decorated with `@step` expecting `SomeEvent`. When `SomeEvent`
    arrives, the dispatcher references `Agent.get_steps_waiting_for_event(SomeEvent)` to locate and run `my_step`.
    """

    @classmethod
    def get_steps(cls):
        """
        Returns all methods on this agent class that are marked as steps.
        A step is identified by the `_is_step` attribute set by the `@step` decorator.
        """
        return [
            method
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
            if getattr(method, "_is_step", False)
        ]

    @classmethod
    def get_steps_waiting_for_event(cls, event_type: Type[ControlEvent]):
        """
        Given an event type, returns the steps that can handle it.
        This helps the dispatcher decide which steps to execute when a certain event arrives.
        """
        steps = cls.get_steps()
        return [method for method in steps if event_type in method._input_events]

    @classmethod
    def get_input_events(cls) -> Set[Type[ControlEvent]]:
        """
        Aggregates all input event types required by all steps.
        This provides a global view of which events can drive the agent’s workflow.
        """
        steps = cls.get_steps()
        return set(event_type for method in steps for event_type in method._input_events)

    @classmethod
    def get_start_events(cls) -> Set[Type[StartEvent]]:
        """
        Returns all event types that are considered start events (subclasses of StartEvent).
        These events indicate how a run/workflow can be initiated.
        """
        input_events = cls.get_input_events()
        return {event for event in input_events if issubclass(event, StartEvent)}

    @classmethod
    def get_stop_events(cls) -> Set[Type[StopEvent]]:
        """
        Returns all event types that are considered stop events (subclasses of StopEvent).
        These events indicate how a run/workflow can terminate.
        """
        input_events = cls.get_input_events()
        return {event for event in input_events if issubclass(event, StopEvent)}
