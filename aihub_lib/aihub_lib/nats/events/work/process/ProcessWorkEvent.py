import inspect
from typing import TypeVar, Generic, Tuple, Type, cast

from aihub_lib.nats.events import ProcessStartEvent, ProcessStopEvent
from aihub_lib.nats.events.utils import get_base_type

TEvent = TypeVar("TEvent", bound=ProcessStopEvent)


class ProcessWorkEvent(ProcessStartEvent, Generic[TEvent]):
    process_stop_event: TEvent

    @classmethod
    def get_stop_event_type(cls) -> Tuple[Type[ProcessStopEvent], ...]:
        """
        Extracts the concrete stop event type(s) from the `agent_event` field.
        This version uses Pydantic's `model_fields` for robust type resolution
        before unwrapping complex type hints.
        """
        if cls is ProcessWorkEvent:
            raise TypeError(
                "Cannot get stop event type from the non-specialized " "generic base class 'ProcessWorkEvent'."
            )

        field_info = cls.model_fields.get("process_stop_event")

        if not field_info or not field_info.annotation:
            raise ValueError(f"Could not find a typed 'process_stop_event' attribute on '{cls.__name__}'.")

        field_annotation = field_info.annotation
        base_types = get_base_type(field_annotation)

        if not base_types:
            raise ValueError(
                f"Unable to extract a base type from the annotation for 'process_stop_event' in '{cls.__name__}'."
            )

        for t in base_types:
            if not inspect.isclass(t):
                raise TypeError(f"Extracted type '{t}' is not a class. " f"Full annotation was '{field_annotation}'.")

        return cast(Tuple[Type[ProcessStopEvent], ...], base_types)