from typing import Type, Set, Dict, Callable, Tuple, Optional
import inspect

from agents_core.workflow.annotations.extractors.extract_event_types import extract_event_types
from lib_core.nats.context.run.RunContext import RunContext
from lib_core.nats.context.thread.ThreadContext import ThreadContext
from lib_core.nats.events import BaseEvent


def extract_function_events(func: Callable) -> Tuple[
    Set[Type[BaseEvent]],
    Dict[str, Set[Type[BaseEvent]]],
    Dict[str, bool],
    Dict[str, Optional[int]]  # New: stores size requirements
]:
    """
    Analyzes a function to determine its input event types.
    Returns a tuple containing:
    - A set of all input event types
    - A mapping from parameter names to event types
    - A mapping from parameter names to optionality
    """
    signature = inspect.signature(func)
    input_events: Set[Type[BaseEvent]] = set()
    input_event_mapping: Dict[str, Set[Type[BaseEvent]]] = {}
    parameter_optional_map: Dict[str, bool] = {}
    size_requirements: Dict[str, Optional[int]] = {}

    for param in signature.parameters.values():
        if param.name == 'self':
            continue
        annotation = param.annotation
        if annotation in (RunContext, ThreadContext):
            continue
        event_types, is_optional, required_size = extract_event_types(annotation)
        if event_types:
            input_events.update(event_types)
            input_event_mapping[param.name] = event_types
            parameter_optional_map[param.name] = is_optional
            size_requirements[param.name] = required_size

    return input_events, input_event_mapping, parameter_optional_map, size_requirements