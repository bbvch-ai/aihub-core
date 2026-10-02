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
    StopEvent,
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
            *cls._outcomes_not_as_declared(blueprint),
            *cls._missing_config_mixins(blueprint, agent_config_type),
            *cls._no_start(blueprint, steps),
            *cls._tools_without_loop(blueprint),
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
        """A call outcome none of the blueprint's own steps picks up leaves the run waiting without a stop event,
        which looks like a hang. Every outcome that does not end the run counts, since the call may answer with any of
        them. The capability's own steps may consume an outcome too (the title does), so only the blueprint's steps
        count, and only for calls made from outside the capability: a tool call the model chose is answered through
        the capability's own adapter step."""
        consumed = {
            event
            for step in blueprint.get_own_steps()
            for event in getattr(step, DispatchableWorkflow.INPUT_EVENTS_ANNOTATION)
        }
        problems = []
        for capability in blueprint.installed_capabilities():
            own = capability.own_steps()
            produced = {
                event
                for step in steps
                if step not in own
                for event in getattr(step, DispatchableWorkflow.OUTPUT_EVENTS_ANNOTATION)
            }
            problems += [
                f"{blueprint.__name__} calls {capability.__name__} with {request.__name__}, but no step consumes its "
                f"result {outcome.__name__}"
                for request, outcomes in capability.calls.items()
                for outcome in outcomes
                if not issubclass(outcome, StopEvent) and request in produced and outcome not in consumed
            ]
        return problems

    @staticmethod
    def _outcomes_not_as_declared(blueprint: type[Agent]) -> list[str]:
        """The declared outcomes are what the blueprint is held to consume, so they must match the capability's steps:
        an outcome no step emits is stale, and a stop event a step can end the call with but nobody declared is a branch
        the blueprint's author cannot see."""
        problems = []
        for capability in blueprint.installed_capabilities():
            for request, outcomes in capability.calls.items():
                emittable = capability.emittable_from(request)
                problems += [
                    f"{capability.__name__} declares {outcome.__name__} as an outcome of {request.__name__}, but none "
                    f"of its steps emits it"
                    for outcome in outcomes
                    if not any(issubclass(event, outcome) for event in emittable)
                ]
                problems += [
                    f"{capability.__name__} can end {request.__name__} with {event.__name__}, but does not declare it "
                    f"as an outcome"
                    for event in emittable
                    if issubclass(event, StopEvent) and not any(issubclass(event, outcome) for outcome in outcomes)
                ]
        return problems

    @staticmethod
    def _tools_without_loop(blueprint: type[Agent]) -> list[str]:
        """Declared tools only ever run inside a tool loop, and a name must mean one tool across the blueprint's sets,
        since a call carries only the name."""
        from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop

        problems = []
        tool_sets = blueprint.tool_sets()
        if tool_sets and ToolLoop not in blueprint.installed_capabilities():
            names = ", ".join(tool_set.name for tool_set in tool_sets)
            problems.append(f"{blueprint.__name__} declares the tool sets {names}, but no step runs one of them")
        sources: dict[str, object] = {}
        for tool_set in tool_sets:
            for name in tool_set.names():
                source = tool_set.source(name)
                if sources.setdefault(name, source) != source:
                    problems.append(f"{blueprint.__name__} declares two different tools named '{name}'")
        return problems

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
