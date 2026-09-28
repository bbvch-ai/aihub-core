import abc
import functools
import inspect
from collections.abc import Callable
from typing import ClassVar

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.agents.agent import Agent


class Capability(abc.ABC):
    """
    A set of steps a blueprint installs by listing the capability on `Agent.capabilities`.

    Steps are `@staticmethod`s decorated with `@step`, taking the blueprint instance as their first
    parameter, so the dispatcher invokes them exactly as it invokes a method defined on the blueprint.
    Composition happens per blueprint in `steps_for`: a capability sees the blueprint it is installed on
    and can withhold a step the blueprint already provides itself, which is how the spine offers defaults
    without a blueprint having to opt out of them.

    `required_config` names the form mixin the capability's steps are annotated with. A blueprint whose
    config does not list it as a base fails at runner start, not on its first run.
    """

    required_config: ClassVar[type[Form]] = Form

    @classmethod
    def steps_for(cls, blueprint: type[Agent]) -> list[Callable]:
        return cls.own_steps()

    @classmethod
    @functools.cache
    def own_steps(cls) -> list[Callable]:
        return [
            method
            for _, method in inspect.getmembers(cls, predicate=inspect.isfunction)
            if getattr(method, Agent.STEP_ANNOTATION, False)
        ]

    @staticmethod
    def produced_events(steps: list[Callable]) -> set[type[BaseEvent]]:
        return {event for step in steps for event in getattr(step, Agent.OUTPUT_EVENTS_ANNOTATION, set())}

    @staticmethod
    def consumed_events(step: Callable) -> set[type[BaseEvent]]:
        return set(getattr(step, Agent.INPUT_EVENTS_ANNOTATION, set()))
