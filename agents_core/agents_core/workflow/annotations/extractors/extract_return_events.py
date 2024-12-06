from typing import Type, Set
import inspect

from lib_core.nats.events import BaseEvent
from agents_core.workflow.annotations.extractors.extract_event_types import extract_event_types


def extract_return_events(func) -> Set[Type[BaseEvent]]:
    """
    Extract the return events from a function based on its annotation.
    Uses the same logic as extract_event_types above.
    """
    return_annotation = func.__signature__.return_annotation
    if return_annotation is inspect._empty:
        return set()
    event_types, _, _ = extract_event_types(return_annotation)
    return event_types
