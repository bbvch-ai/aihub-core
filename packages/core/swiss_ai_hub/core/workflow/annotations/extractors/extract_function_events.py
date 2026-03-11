import inspect
from collections.abc import Callable
from typing import Annotated

from swiss_ai_hub.core.events.BaseEvent import BaseEvent
from swiss_ai_hub.core.workflow.annotations.extractors.extract_event_classes import extract_event_classes
from swiss_ai_hub.core.workflow.annotations.extractors.extract_return_events import extract_return_events


def extract_function_events(
    func: Annotated[
        Callable,
        "A function or method whose parameters are to be analyzed for event types.",
    ],
) -> tuple[
    set[type[BaseEvent]],
    set[type[BaseEvent]],
    dict[str, set[type[BaseEvent]]],
    dict[str, bool],
    dict[str, int | None],
]:
    """
    Analyze a function’s parameters to determine which event types it consumes, as well as optionality
    and size constraints for these events.

    ### Why This Function?
    Steps in a workflow often have type-annotated parameters indicating what kinds of events they expect.
    By inspecting these annotations, you can programmatically derive what a workflow step needs:
    - Which events must be provided?
    - Are certain parameters optional?
    - If a parameter expects a fixed-size collection of events, what is that size?

    ### Returns
    A tuple of:
    1. `input_events`: A set of all input event types referenced by the function.
    2. `input_event_mapping`: A dict mapping parameter names to the set of event types they accept.
    3. `parameter_optional_map`: A dict mapping parameter names to a boolean indicating if `None` is allowed.
    4. `size_requirements`: A dict mapping parameter names to an integer size if a fixed-size collection is required,
      or None otherwise.

    ### Details
    - Parameters named `self` are ignored (common in instance methods).
    - Parameters annotated as `RunContext` or `ThreadContext` are not event parameters and thus skipped.
    - Uses `extract_event_classes` internally to handle complex union types, optional parameters,
      and fixed-size collections.

    ### Example
    Consider a step method:
    ```python
    def my_step(event: SomeEvent | None, events: list[AnotherEvent], fixed: Fixedlist[YetAnotherEvent, 3]) -> StopEvent:
        ...
    ```
    This might produce:
    - input_events = {SomeEvent, AnotherEvent, YetAnotherEvent}
    - output_events = {StopEvent}
    - input_event_mapping = {"event": {SomeEvent}, "events": {AnotherEvent}, "fixed": {YetAnotherEvent}}
    - parameter_optional_map = {"event": True, "events": False, "fixed": False}
    - size_requirements = {"event": None, "events": None, "fixed": 3}
    """

    signature = inspect.signature(func)
    input_events: set[type[BaseEvent]] = set()
    input_event_mapping: dict[str, set[type[BaseEvent]]] = {}
    parameter_optional_map: dict[str, bool] = {}
    size_requirements: dict[str, int | None] = {}

    output_events: set[type[BaseEvent]] = extract_return_events(func)

    for param in signature.parameters.values():
        if param.name == "self":
            continue
        annotation = param.annotation

        event_classes, is_optional, required_size = extract_event_classes(annotation)
        if event_classes:
            input_events.update(event_classes)
            input_event_mapping[param.name] = event_classes
            parameter_optional_map[param.name] = is_optional
            size_requirements[param.name] = required_size

    return input_events, output_events, input_event_mapping, parameter_optional_map, size_requirements
