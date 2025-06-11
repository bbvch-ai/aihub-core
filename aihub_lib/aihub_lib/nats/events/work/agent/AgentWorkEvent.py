import inspect
from typing import Annotated, Optional, Tuple, Type, Union, get_args, get_origin

from aihub_lib.nats.events import ControlEvent, StopEvent
from aihub_lib.nats.events.work.WorkEvent import WorkEvent


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


class AgentWorkEvent(WorkEvent):
    agent_event: StopEvent

    @classmethod
    def get_stop_event_type(cls) -> Optional[Type[ControlEvent] | Tuple[Type[ControlEvent]]]:
        annotations = inspect.get_annotations(cls, eval_str=True)

        if "agent_event" not in annotations:
            return None

        field_annotation = annotations["agent_event"]
        return get_base_type(field_annotation)
