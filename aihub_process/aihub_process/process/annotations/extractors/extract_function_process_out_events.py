import inspect
from typing import Annotated, List, Tuple, Type, get_args, get_origin

from aihub_lib.nats.events import WorkRequestEvent
from aihub_lib.nats.workflow.annotations.extractors.extract_event_names import extract_event_classes

from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


def extract_function_process_out_events(func) -> List[Tuple[Type[WorkRequestEvent], BaseProcessEntity.Out]]:
    """
    Analyzes a process step function's signature to extract and validate its output events.

    This function enforces strict rules for process step outputs:
    - The return type MUST be `None`, `type(None)`, or an `Annotated` type.
    - Return annotations MUST contain a `BaseProcessEntity.Out` configuration object.
    - The core type of a return value MUST be a subclass of `WorkRequestEvent`.
    """
    sig = inspect.signature(func)
    output_tuples = []
    return_annotation = sig.return_annotation

    if return_annotation in (None, type(None), inspect.Signature.empty):
        return []

    if get_origin(return_annotation) is not Annotated:
        raise TypeError(
            f"In process step '{func.__name__}', the return type is not valid. "
            f"It must be None or Annotated[WorkRequestEvent, Config.Out]."
        )

    core_type, *metadata = get_args(return_annotation)
    config_instance = next((m for m in metadata if isinstance(m, BaseProcessEntity.Out)), None)

    if not config_instance:
        raise TypeError(
            f"In process step '{func.__name__}', the return type is missing a .Out configuration "
            f"(e.g., Program.Out(...), Agent.Out(...))."
        )

    event_classes, _, _ = extract_event_classes(core_type)
    if not event_classes:
        raise TypeError(f"Could not extract a valid event type from return annotation in '{func.__name__}'.")

    for event_cls in event_classes:
        if not issubclass(event_cls, WorkRequestEvent):
            raise TypeError(
                f"In process step '{func.__name__}', the return event type '{event_cls.__name__}' "
                f"is not a subclass of WorkRequestEvent."
            )
        output_tuples.append((event_cls, config_instance))

    return output_tuples
