import inspect
from typing import Annotated, Generic, List, Tuple, Type, TypeVar, Union, cast, get_args, get_origin

from aihub_lib.nats.events import StopEvent
from aihub_lib.nats.events.work.WorkEvent import WorkEvent
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize


def get_base_type(annotation: Type) -> Tuple[Type, ...]:
    """
    Recursively unwraps a type hint to find the core, non-wrapper type(s).
    """
    origin = get_origin(annotation)

    # Case 1: Annotated[T, ...]
    if origin is Annotated:
        return get_base_type(get_args(annotation)[0])

    # Case 2: Union[A, B, ...] or Optional[A]
    if origin is Union:
        base_types: List[Type] = []
        for arg in get_args(annotation):
            if arg is not type(None):
                base_types.extend(get_base_type(arg))
        return tuple(base_types)

    # Case 3: list[T] or a custom generic like ListOfSize[T, ...]
    is_list_like = isinstance(origin, type) and issubclass(origin, list)
    if origin is list or origin is ListOfSize or is_list_like:
        return get_base_type(get_args(annotation)[0])

    if isinstance(annotation, type):
        return (annotation,)

    return (annotation,)


TEvent = TypeVar("TEvent", bound=StopEvent)


class AgentWorkEvent(WorkEvent, Generic[TEvent]):
    agent_event: TEvent

    @classmethod
    def get_stop_event_type(cls) -> Tuple[Type[StopEvent], ...]:
        """
        Extracts the concrete stop event type(s) from the `agent_event` field.
        This version uses Pydantic's `model_fields` for robust type resolution
        before unwrapping complex type hints.
        """
        if cls is AgentWorkEvent:
            raise TypeError(
                "Cannot get stop event type from the non-specialized " "generic base class 'AgentWorkEvent'."
            )

        field_info = cls.model_fields.get("agent_event")

        if not field_info or not field_info.annotation:
            raise ValueError(f"Could not find a typed 'agent_event' attribute on '{cls.__name__}'.")

        field_annotation = field_info.annotation
        base_types = get_base_type(field_annotation)

        if not base_types:
            raise ValueError(
                f"Unable to extract a base type from the annotation for 'agent_event' in '{cls.__name__}'."
            )

        for t in base_types:
            if not inspect.isclass(t):
                raise TypeError(f"Extracted type '{t}' is not a class. " f"Full annotation was '{field_annotation}'.")

        return cast(Tuple[Type[StopEvent], ...], base_types)
