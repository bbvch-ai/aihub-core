import inspect
from typing import Annotated, get_args, get_origin

from swiss_ai_hub.core.events.process import ProcessStopEvent
from swiss_ai_hub.core.events.process import WorkRequestEvent

from swiss_ai_hub.process.delegators.abstract_process_entity import BaseProcessEntity


def extract_function_process_out_events(func) -> list[tuple[type[WorkRequestEvent], BaseProcessEntity.Out]]:
    """
    Analyzes a process step function's signature to extract its output events
    under a strict contract.

    This version handles `tuple[Annotated[...]]` returns and enforces that
    each `Annotated` item contains exactly one event type (not a Union or List).
    """
    sig = inspect.signature(func)
    return_annotation = sig.return_annotation
    all_output_tuples = []

    if return_annotation in (None, type(None), inspect.Signature.empty):
        return []

    origin = get_origin(return_annotation)

    if origin in (tuple, tuple):
        annotations_to_process = get_args(return_annotation)
    else:
        annotations_to_process = [return_annotation]

    for i, annotation_item in enumerate(annotations_to_process):
        if get_origin(annotation_item) is not Annotated:
            raise TypeError(
                f"In process step '{func.__name__}', the return type is not valid. "
                f"It must be None, Annotated[...], or a Tuple of Annotated[...]."
            )

        core_type, *metadata = get_args(annotation_item)
        config_instance = next((m for m in metadata if isinstance(m, BaseProcessEntity.Out)), None)

        if not config_instance:
            raise TypeError(
                f"In process step '{func.__name__}', the return annotation at "
                f"index {i} is missing a .Out configuration."
            )

        # 1. Disallow containers (List, Dict) and special types (Union).
        # A simple class like `AgentBWorkRequest` will have an origin of `None`.
        if get_origin(core_type) is not None:
            raise TypeError(
                f"In process step '{func.__name__}', the output at index {i} is invalid. "
                f"Each Annotated type must contain a single event class, not a complex type like "
                f"'{get_origin(core_type).__name__}' or a Union."
            )

        # 2. Ensure the type is a class and a valid subclass of our event base classes.
        if not inspect.isclass(core_type) or not issubclass(core_type, WorkRequestEvent | ProcessStopEvent):
            raise TypeError(
                f"In process step '{func.__name__}', the output type '{core_type.__name__}' at index {i} "
                f"is not a valid subclass of WorkRequestEvent or ProcessStopEvent."
            )

        event_cls = core_type
        all_output_tuples.append((event_cls, config_instance))

    return all_output_tuples
