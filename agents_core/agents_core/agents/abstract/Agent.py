import abc
from typing import Type
import inspect

from lib_core.nats.events import ControlEvent


class Agent(abc.ABC):
    """Base class for agents that process events through steps."""

    @classmethod
    def get_steps(cls):
        return [
            method for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
            if getattr(method, '_is_step', False)
        ]

    @classmethod
    def get_steps_waiting_for_event(cls, event_type: Type[ControlEvent]):
        steps = cls.get_steps()
        return [
            method for method in steps
            if event_type in method._input_events
        ]