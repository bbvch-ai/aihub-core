import inspect
from collections.abc import Callable
from typing import Self

from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoopExceptionEvent,
    AgentInTheLoopResponseEvent,
    BotInTheLoopResponseEvent,
    HumanInTheLoopResponseEvent,
    StartEvent,
)
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.workflow import DispatchableWorkflow

from swiss_ai_hub.agent.agents.agent import Agent

# Events a run receives from outside its own steps: the start, and the answers to the loops it opened.
ARRIVES_FROM_OUTSIDE: tuple[type[BaseEvent], ...] = (
    StartEvent,
    HumanInTheLoopResponseEvent,
    AgentInTheLoopResponseEvent,
    AgentInTheLoopExceptionEvent,
    BotInTheLoopResponseEvent,
)


class WorkflowValidation:
    """
    Every way a composed workflow can stall or crash before its first run, found at startup instead.

    The dispatcher cannot tell a step that is waiting for an event from a step whose event nobody will ever
    produce, so a blueprint that calls a capability but never consumes its result, or forgets the mixin the
    capability's steps are annotated with, would hang or crash on its first message. This walks the composed
    step set once and names every such gap with what to do about it.
    """

    def __init__(self, blueprint: type[Agent], problems: list[str]):
        self.blueprint = blueprint
        self.problems = problems

    @classmethod
    def for_blueprint(cls, blueprint: type[Agent], agent_config_type: type[AgentConfig]) -> Self:
        steps = blueprint.get_steps()
        problems = [
            *cls._duplicate_step_names(blueprint, steps),
            *cls._inputs_nobody_produces(blueprint, steps),
            *cls._results_nobody_consumes(blueprint, steps),
            *cls._missing_config_mixins(blueprint, agent_config_type),
            *cls._no_start(blueprint, steps),
        ]
        return cls(blueprint, problems)

    def raise_for_problems(self) -> None:
        if self.problems:
            raise ValueError(f"{self.blueprint.__name__} cannot run:\n- " + "\n- ".join(self.problems))

    @staticmethod
    def _duplicate_step_names(blueprint: type[Agent], steps: list[Callable]) -> list[str]:
        """Step identity is the function name everywhere downstream, so two steps sharing one would dedupe
        each other's executions."""
        seen: dict[str, Callable] = {}
        problems = []
        for step in steps:
            if step.__name__ in seen:
                problems.append(
                    f"two steps are named '{step.__name__}' ({_origin(seen[step.__name__])} and {_origin(step)})"
                )
            seen[step.__name__] = step
        return problems

    @classmethod
    def _inputs_nobody_produces(cls, blueprint: type[Agent], steps: list[Callable]) -> list[str]:
        produced = {event for step in steps for event in getattr(step, DispatchableWorkflow.OUTPUT_EVENTS_ANNOTATION)}
        problems = []
        for step in steps:
            mapping: dict[str, set[type[BaseEvent]]] = getattr(
                step, DispatchableWorkflow.INPUT_EVENT_MAPPING_ANNOTATION
            )
            optional: dict[str, bool] = getattr(step, DispatchableWorkflow.PARAMETER_OPTIONAL_MAP_ANNOTATION)
            for parameter, events in mapping.items():
                if optional.get(parameter, False):
                    continue
                if any(event in produced or issubclass(event, ARRIVES_FROM_OUTSIDE) for event in events):
                    continue
                names = " | ".join(sorted(event.__name__ for event in events))
                problems.append(
                    f"{_origin(step)} waits for '{parameter}: {names}', but no step on {blueprint.__name__} produces "
                    f"it, so the run would stall there"
                )
        return problems

    @staticmethod
    def _results_nobody_consumes(blueprint: type[Agent], steps: list[Callable]) -> list[str]:
        """A call whose result none of the blueprint's own steps picks up ends the run without a stop event, which
        looks like a hang. The capability's own steps may consume the result too (the title does), so only the
        blueprint's steps count."""
        produced = {event for step in steps for event in getattr(step, DispatchableWorkflow.OUTPUT_EVENTS_ANNOTATION)}
        consumed = {
            event
            for step in blueprint.get_own_steps()
            for event in getattr(step, DispatchableWorkflow.INPUT_EVENTS_ANNOTATION)
        }
        return [
            f"{blueprint.__name__} calls {capability.__name__} with {request.__name__}, but no step consumes its "
            f"result {result.__name__}"
            for capability in blueprint.installed_capabilities()
            for request, result in capability.calls.items()
            if result is not None and request in produced and result not in consumed
        ]

    @staticmethod
    def _missing_config_mixins(blueprint: type[Agent], agent_config_type: type[AgentConfig]) -> list[str]:
        return [
            f"{capability.__name__} is called, so {agent_config_type.__name__} must list "
            f"{capability.required_config.__name__} as a base"
            for capability in blueprint.installed_capabilities()
            if not issubclass(agent_config_type, capability.required_config)
        ]

    @staticmethod
    def _no_start(blueprint: type[Agent], steps: list[Callable]) -> list[str]:
        if blueprint.get_start_events():
            return []
        return [f"no step on {blueprint.__name__} consumes a start event"]


def _origin(step: Callable) -> str:
    owner = inspect.getmodule(step)
    qualname = getattr(step, "__qualname__", step.__name__)
    return f"{owner.__name__.rsplit('.', 1)[-1]}.{qualname}" if owner else qualname
