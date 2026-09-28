from collections.abc import Callable

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.workflow import DispatchableWorkflow

from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.workflow.workflow_validation import ARRIVES_FROM_OUTSIDE


class CapabilityCatalog:
    """The capabilities the SDK ships, and how a blueprint's own steps pull their steps in."""

    @staticmethod
    def all() -> list[type[Capability]]:
        from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
        from swiss_ai_hub.agent.capabilities.memory.memory import Memory

        return [Conversation, Memory]

    @classmethod
    def called_by(cls, steps: list[Callable]) -> list[type[Capability]]:
        """The capabilities whose request events these steps produce, transitively: a capability's own steps may
        call another capability."""
        installed: list[type[Capability]] = []
        produced: set[type[BaseEvent]] = Capability.produced_events(steps)
        changed = True
        while changed:
            changed = False
            for capability in cls.all():
                if capability in installed or not (capability.handles() & produced):
                    continue
                installed.append(capability)
                produced |= Capability.produced_events(capability.own_steps())
                changed = True
        return installed

    @classmethod
    def reachable_steps(cls, own_steps: list[Callable]) -> list[Callable]:
        """The capability steps that can actually run for this blueprint: a call it never makes, and everything
        downstream of that call, stays out of the workflow rather than dangling in the graph."""
        candidates = [step for capability in cls.called_by(own_steps) for step in capability.own_steps()]
        reachable: list[Callable] = []
        produced = Capability.produced_events(own_steps)
        changed = True
        while changed:
            changed = False
            for step in candidates:
                if step in reachable or not _can_be_triggered(step, produced):
                    continue
                reachable.append(step)
                produced |= Capability.produced_events([step])
                changed = True
        return reachable


def _can_be_triggered(step: Callable, produced: set[type[BaseEvent]]) -> bool:
    mapping: dict[str, set[type[BaseEvent]]] = getattr(step, DispatchableWorkflow.INPUT_EVENT_MAPPING_ANNOTATION)
    optional: dict[str, bool] = getattr(step, DispatchableWorkflow.PARAMETER_OPTIONAL_MAP_ANNOTATION)
    required = [events for parameter, events in mapping.items() if not optional.get(parameter, False)]
    return any(event in produced or issubclass(event, ARRIVES_FROM_OUTSIDE) for events in required for event in events)
