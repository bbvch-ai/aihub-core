import abc
import functools
import inspect
from collections.abc import Callable
from typing import ClassVar

from swiss_ai_hub.core.events.agent import ChatFeature
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

    # The calls this capability answers: request event -> every outcome the call can end in. A call may answer
    # with one of several events, or end the run (a stop event outcome). Returning a request from a step is what
    # composes the capability's steps into the blueprint's workflow; the blueprint must consume every outcome that
    # is not a stop event, and validation checks the outcomes against what the capability's steps can emit.
    calls: ClassVar[dict[type[ControlEvent], tuple[type[ControlEvent], ...]]] = {}

    # The chat feature this capability serves, if any. A blueprint supports exactly the features of the
    # capabilities it installs, which is what chat clients use to decide which toggles to show.
    chat_feature: ClassVar[ChatFeature | None] = None

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

    @classmethod
    def emittable_from(cls, request: type[ControlEvent]) -> set[type[BaseEvent]]:
        """Every event the capability's own steps can emit once the request arrives, following its internal chain."""
        produced: set[type[BaseEvent]] = {request}
        reached: list[Callable] = []
        changed = True
        while changed:
            changed = False
            for step in cls.own_steps():
                if step in reached or not produced & getattr(step, Agent.INPUT_EVENTS_ANNOTATION, set()):
                    continue
                reached.append(step)
                produced |= set(getattr(step, Agent.OUTPUT_EVENTS_ANNOTATION, set()))
                changed = True
        return produced - {request}

    @staticmethod
    def produced_events(steps: list[Callable]) -> set[type[BaseEvent]]:
        return {event for step in steps for event in getattr(step, Agent.OUTPUT_EVENTS_ANNOTATION, set())}
