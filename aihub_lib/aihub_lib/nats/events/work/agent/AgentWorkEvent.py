import inspect
from typing import Annotated, Optional, Tuple, Type, Union, get_args, get_origin, TypeVar, Generic, get_type_hints

from aihub_lib.nats.events import ControlEvent, StopEvent
from aihub_lib.nats.events.work.WorkEvent import WorkEvent
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize


def get_base_type(annotation: Type) -> Type | tuple[Type, ...]:
    """
    Recursively unwraps a type hint to find the core type(s).

    This handles:
    - Annotated[T, ...]: Returns the base type of T.
    - Optional[T] / Union[T, ...]: Returns the non-NoneType base types.
    """
    origin = get_origin(annotation)

    # Case 1: The type is Annotated[T, ...]. We care about T.
    if origin is Annotated:
        # The actual type is the first argument, so we recurse on it.
        return get_base_type(get_args(annotation)[0])

    # Case 2: The type is Optional[T] or Union[T, U, ...].
    if origin is Union:
        # Filter out NoneType and find the base type for all other arguments.
        base_types = []
        for arg in get_args(annotation):
            if arg is not type(None):
                base_types.append(get_base_type(arg))

        # If only one type remains (e.g., from Optional[T]), return it directly.
        # Otherwise, return all found base types as a tuple.
        return base_types[0] if len(base_types) == 1 else tuple(base_types)

    # Case 3: It's a simple, non-wrapper type. This is our base case.
    return annotation


TEvent = TypeVar("TEvent", bound=StopEvent)

class AgentWorkEvent(WorkEvent, Generic[TEvent]):
    agent_event: TEvent

    @classmethod
    def get_stop_event_type(cls) -> Tuple[Type[TEvent], ...]:
        """
        Correctly and robustly extracts the concrete type(s) used to specialize
        TEvent in any subclass.
        """
        # This check prevents calling on the generic base class itself.
        if cls is AgentWorkEvent:
            raise TypeError(
                "Cannot get stop event type from the non-specialized "
                "generic base class 'AgentWorkEvent'."
            )

        # __orig_bases__ holds the base classes with their generic types intact.
        # e.g., for AgentAWork, it contains AgentWorkEvent[AgentAStopEvent]
        print("orig_bases", getattr(cls, "__orig_bases__", []))
        for base in getattr(cls, "__orig_bases__", []):
            # get_origin gets the base generic type (e.g., AgentWorkEvent)
            if get_origin(base) is AgentWorkEvent:
                # get_args gets the types used in the specialization
                # e.g., (AgentAStopEvent,)
                args = get_args(base)
                if args:
                    # We found the specialization. Return the concrete types.
                    return args

        raise ValueError(
            f"Could not determine the concrete type for TEvent in class '{cls.__name__}'. "
            f"Ensure '{cls.__name__}' inherits from AgentWorkEvent[SomeStopEventClass]."
        )
