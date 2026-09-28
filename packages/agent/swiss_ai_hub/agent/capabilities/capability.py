import abc
import functools
import inspect
from collections.abc import Callable
from typing import ClassVar

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.agents.agent import Agent


class Capability(abc.ABC):
    """
    A sub-workflow a blueprint calls by returning one of its request events and picks up again by consuming
    the matching result event, the way `HumanInTheLoop` and `AgentInTheLoop` work.

    A capability exposes typed helpers that build its request events (`Conversation.contextualize(...)`,
    `Memory.recall(...)`), and its steps are `@staticmethod`s decorated with `@step` that take the blueprint
    instance as their first parameter, so the dispatcher invokes them exactly as it invokes a method. Nothing is
    installed by listing: a blueprint whose steps return a capability's request event has that capability's
    steps composed into `get_steps()`, and the run's config is checked to carry `required_config`.
    """

    # The calls this capability answers: request event -> result event, or None when the call ends the run.
    # Returning a request from a step is what composes the capability's steps into the blueprint's workflow,
    # and the result is what the blueprint must consume to pick the call up again.
    calls: ClassVar[dict[type[ControlEvent], type[ControlEvent] | None]] = {}

    @classmethod
    def handles(cls) -> frozenset[type[ControlEvent]]:
        return frozenset(cls.calls)

    # The form mixin the capability's steps are annotated with; the blueprint's config must list it as a base.
    required_config: ClassVar[type[Form]] = Form

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
