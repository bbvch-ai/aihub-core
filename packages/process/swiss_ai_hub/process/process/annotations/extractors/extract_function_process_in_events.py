import inspect
from typing import Annotated, get_args, get_origin

from swiss_ai_hub.core.nats.events.work.WorkEvent import WorkEvent
from swiss_ai_hub.core.nats.workflow.annotations.extractors.extract_event_classes import extract_event_classes

from swiss_ai_hub.process.delegators.AbstractProcessEntity import BaseProcessEntity


def extract_function_process_in_events(func) -> list[tuple[type[WorkEvent], BaseProcessEntity.In]]:
    """
    Analyzes a process step function's signature to extract and validate its input events.

    This function enforces strict rules for process step inputs:
    - All input parameters (except 'self') MUST be Annotated.
    - Input annotations MUST contain a `BaseProcessEntity.In` configuration object.
    - The core type of an input MUST be a subclass of `WorkEvent`.
    """
    sig = inspect.signature(func)
    input_tuples = []

    for param in sig.parameters.values():
        if param.name == "self":
            continue

        annotation = param.annotation

        if get_origin(annotation) is not Annotated:
            raise TypeError(
                f"In process step '{func.__name__}', parameter '{param.name}' is not Annotated. "
                f"All process inputs must be wrapped in Annotated[EventType, Config]."
            )

        core_type, *metadata = get_args(annotation)
        config_instance = next((m for m in metadata if isinstance(m, BaseProcessEntity.In)), None)

        if not config_instance:
            raise TypeError(
                f"In process step '{func.__name__}', parameter '{param.name}' is missing a .In configuration "
                f"(e.g., Program.In(...), Agent.In(...))."
            )

        event_classes, _, _ = extract_event_classes(core_type)
        if not event_classes:
            raise TypeError(f"Could not extract a valid event type from parameter '{param.name}' in '{func.__name__}'.")

        for event_cls in event_classes:
            if not issubclass(event_cls, WorkEvent):
                raise TypeError(
                    f"In process step '{func.__name__}', the event type '{event_cls.__name__}' for parameter "
                    f"'{param.name}' is not a subclass of WorkEvent."
                )
            input_tuples.append((event_cls, config_instance))

    return input_tuples
