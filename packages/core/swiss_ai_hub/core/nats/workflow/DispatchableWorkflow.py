import abc
import functools
import inspect
from collections.abc import Callable

from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent
from swiss_ai_hub.core.nats.events.work.WorkEvent import WorkEvent


class DispatchableWorkflow(abc.ABC):
    """
    Within the aihub, multiple different entities follow event-driven execution patterns, namely Agents and Processes.

    For an entity to be event-driven, it means that it defines a set of steps that will be executed if a certain
    set of conditions is satisfied, most often linked to the presence of certain events.

    Such an entity is called a "dispatchable workflow", because the entity that will coordinate the
    execution of its steps with the reception of events is called the "dispatcher".

    In a minimal implementation, a dispatchable workflow is defined by a set of methods that are marked as steps.
    Note that the class of a dispatchable workflow itself must be stateless, as the state of the class is indirectly
    given through the events it receives and hence coordinated by the dispatcher.

    The abstract DispatchableWorkflow class provides a set of utility methods that can be used to extract information
    from dispatchable workflow classes, such as the set of steps, the set of input events, and the set of output events.
    """

    # Defines what attribute must be present on a method to be considered a dispatchable workflow step
    STEP_ANNOTATION = "_is_step"

    STEP_NAME_ANNOTATION = "_step_name"
    STEP_DESCRIPTION_ANNOTATION = "_step_description"
    STEP_ICON_ANNOTATION = "_step_icon"

    SIGNATURE_ANNOTATION = "__signature__"

    INPUT_EVENT_MAPPING_ANNOTATION = "_input_event_mapping"
    PARAMETER_OPTIONAL_MAP_ANNOTATION = "_parameter_optional_map"
    SIZE_REQUIREMENT_ANNOTATION = "_size_requirements"

    INPUT_EVENTS_ANNOTATION = "_input_events"
    OUTPUT_EVENTS_ANNOTATION = "_output_events"

    @classmethod
    @functools.cache
    def get_steps(cls) -> list[Callable]:
        """
        Returns all methods on this dispatchable workflow that are marked as steps.
        A step is identified by the `STEP_ANNOTATION` attribute set by the `@step` or `@process_step` decorator.
        """
        return [
            method
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
            if getattr(method, cls.STEP_ANNOTATION, False)
        ]

    @classmethod
    @functools.cache
    def get_steps_waiting_for_event(cls, event_class: type[ControlEvent] | type[WorkEvent]) -> list[Callable]:
        """
        Given an event type, returns the steps that can handle it.
        This helps the dispatcher decide which steps to execute when a certain event arrives.
        """
        steps = cls.get_steps()
        return [method for method in steps if event_class in getattr(method, cls.INPUT_EVENTS_ANNOTATION)]

    @classmethod
    @functools.cache
    def get_input_events(cls) -> set[type[ControlEvent]]:
        """
        Aggregates all input event types required by all steps.
        This provides a global view of which events can drive the workflow.
        """
        steps = cls.get_steps()
        return set(event_class for method in steps for event_class in getattr(method, cls.INPUT_EVENTS_ANNOTATION))

    @classmethod
    @functools.cache
    def get_output_events(cls) -> set[type[ControlEvent]]:
        """
        Aggregates all output event types produced by all steps.
        This provides a global view of which events the can emit.
        """
        steps = cls.get_steps()
        return set(event_class for method in steps for event_class in getattr(method, cls.OUTPUT_EVENTS_ANNOTATION))
