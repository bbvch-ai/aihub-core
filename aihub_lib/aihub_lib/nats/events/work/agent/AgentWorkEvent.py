import inspect
from typing import Generic, Tuple, Type, TypeVar, cast

from aihub_lib.nats.events import StopEvent
from aihub_lib.nats.events.utils import get_base_type
from aihub_lib.nats.events.work.WorkEvent import WorkEvent

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
