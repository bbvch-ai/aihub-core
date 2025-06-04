import abc
import functools
import inspect
from typing import Callable, List, Set, Type

from aihub_lib.nats.events import ControlEvent


class DispatchableWorkflow(abc.ABC):
    @classmethod
    @functools.cache
    def get_steps(cls) -> List[Callable]:
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
    @functools.cache
    def get_steps_waiting_for_event(cls, event_class: Type[ControlEvent]) -> List[Callable]:
        """
        Given an event type, returns the steps that can handle it.
        This helps the dispatcher decide which steps to execute when a certain event arrives.
        """
        steps = cls.get_steps()
        return [method for method in steps if event_class in method._input_events]

    @classmethod
    @functools.cache
    def get_input_events(cls) -> Set[Type[ControlEvent]]:
        """
        Aggregates all input event types required by all steps.
        This provides a global view of which events can drive the agent’s workflow.
        """
        steps = cls.get_steps()
        return set(event_class for method in steps for event_class in method._input_events)

    @classmethod
    @functools.cache
    def get_output_events(cls) -> Set[Type[ControlEvent]]:
        """
        Aggregates all output event types produced by all steps.
        This provides a global view of which events the agent can emit.
        """
        steps = cls.get_steps()
        return set(event_class for method in steps for event_class in method._output_events)
