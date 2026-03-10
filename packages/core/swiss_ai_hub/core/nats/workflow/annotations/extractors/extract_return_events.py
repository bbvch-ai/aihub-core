import inspect
from collections.abc import Callable
from typing import Annotated

from swiss_ai_hub.core.nats.events.BaseEvent import BaseEvent
from swiss_ai_hub.core.nats.workflow.annotations.extractors.extract_event_classes import extract_event_classes


def extract_return_events(
    func: Annotated[
        Callable,
        "A function or method whose return type is to be analyzed for event types.",
    ],
) -> set[type[BaseEvent]]:
    """
    Determine which event types a function produces based on its return annotation.

    ### Why This Function?
    Just like parameters can indicate which events a function consumes, the return annotation can
    suggest which events a function emits. By examining the return type (which might be a single event,
    a union of events, optional events, or event collections), we can understand what kind of output
    the workflow step may produce.

    ### How It Works
    - Retrieves the function’s return annotation from `func.__signature__.return_annotation`.
    - Passes that annotation to `extract_event_classes` to handle unions, optionals, fixed-size lists, etc.
    - Returns a set of `BaseEvent` subclasses that represent possible output events.

    ### Note
    If the function lacks a return annotation (or if it's `inspect._empty`), this method returns an empty set.

    ### Example
    For:
    ```python
    def my_step(...) -> SomeEvent | None:
        ...
    ```
    This would return `{SomeEvent}` indicating that it may return a `SomeEvent` or `None`.
    """
    signature = inspect.signature(func)
    return_annotation = signature.return_annotation
    if return_annotation is inspect._empty:
        return set()

    event_classes, _, _ = extract_event_classes(return_annotation)
    return event_classes
