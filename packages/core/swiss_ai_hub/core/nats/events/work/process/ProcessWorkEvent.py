import inspect
from typing import Annotated, TypeVar, cast

from pydantic import Field

from swiss_ai_hub.core.nats.events import ProcessStartEvent, ProcessStopEvent
from swiss_ai_hub.core.nats.events.utils import get_base_type

TEvent = TypeVar("TEvent", bound=ProcessStopEvent)


class ProcessWorkEvent[TEvent: ProcessStopEvent](ProcessStartEvent):
    """
    Signals a piece of work completed by another process.
    As this work event is generated automatically by the process delegator, you can't really add attributes to this
    class.
    The delegator will add the stop event type to the `process_stop_event` field, making the output information
    from the process work accessible for you to use in your process.
    Note that this event is a ProcessStartEvent, as processes can start other processes, but not be part of other
    processes.
    """

    process_stop_event: Annotated[TEvent, Field(description="The stop event of the process that completed the work.")]

    @classmethod
    def get_stop_event_type(cls) -> tuple[type[ProcessStopEvent], ...]:
        """
        Extracts the concrete stop event type(s) from the `agent_stop_event` field.
        This version uses Pydantic's `model_fields` for robust type resolution
        before unwrapping complex type hints.
        """
        if cls is ProcessWorkEvent:
            raise TypeError(
                "Cannot get stop event type from the non-specialized generic base class 'ProcessWorkEvent'."
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
                raise TypeError(f"Extracted type '{t}' is not a class. Full annotation was '{field_annotation}'.")

        return cast(tuple[type[ProcessStopEvent], ...], base_types)
