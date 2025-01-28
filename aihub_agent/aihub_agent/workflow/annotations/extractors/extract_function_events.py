import inspect
from typing import Annotated, Callable, Dict, Optional, Set, Tuple, Type

from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.context.thread.ThreadContext import ThreadContext
from aihub_lib.nats.events import BaseEvent

from aihub_agent.workflow.annotations.extractors.extract_event_types import extract_event_types


def extract_function_events(
    func: Annotated[
        Callable,
        "A function or method whose parameters are to be analyzed for event types.",
    ],
) -> Tuple[
    Set[Type[BaseEvent]],
    Dict[str, Set[Type[BaseEvent]]],
    Dict[str, bool],
    Dict[str, Optional[int]],
]:
    """
    Analyze a function’s parameters to determine which event types it consumes, as well as optionality
    and size constraints for these Events.

    ### Why This Function?
    Steps in a workflow often have type-annotated parameters indicating what kinds of Events they expect.
    By inspecting these annotations, you can programmatically derive what a workflow step needs:
    - Which Events must be provided?
    - Are certain parameters optional?
    - If a parameter expects a fixed-size collection of Events, what is that size?

    ### Returns
    A tuple of:
    1. `input_events`: A set of all input event types referenced by the function.
    2. `input_event_mapping`: A dict mapping parameter names to the set of event types they accept.
    3. `parameter_optional_map`: A dict mapping parameter names to a boolean indicating if `None` is allowed.
    4. `size_requirements`: A dict mapping parameter names to an integer size if a fixed-size collection is required, or None otherwise.

    ### Details
    - Parameters named `self` are ignored (common in instance methods).
    - Parameters annotated as `RunContext` or `ThreadContext` are not event parameters and thus skipped.
    - Uses `extract_event_types` internally to handle complex union types, optional parameters, and fixed-size collections.

    ### Example
    Consider a step method:
    ```python
    def my_step(event: SomeEvent | None, Events: List[AnotherEvent], fixed: FixedList[YetAnotherEvent, 3]):
        ...
    ```
    This might produce:
    - input_events = {SomeEvent, AnotherEvent, YetAnotherEvent}
    - input_event_mapping = {"event": {SomeEvent}, "Events": {AnotherEvent}, "fixed": {YetAnotherEvent}}
    - parameter_optional_map = {"event": True, "Events": False, "fixed": False}
    - size_requirements = {"event": None, "Events": None, "fixed": 3}
    """

    signature = inspect.signature(func)
    input_events: Set[Type[BaseEvent]] = set()
    input_event_mapping: Dict[str, Set[Type[BaseEvent]]] = {}
    parameter_optional_map: Dict[str, bool] = {}
    size_requirements: Dict[str, Optional[int]] = {}

    for param in signature.parameters.values():
        if param.name == "self":
            continue
        annotation = param.annotation
        # Skip run/thread context params, not considered event inputs
        if annotation in (RunContext, ThreadContext):
            continue

        event_types, is_optional, required_size = extract_event_types(annotation)
        if event_types:
            input_events.update(event_types)
            input_event_mapping[param.name] = event_types
            parameter_optional_map[param.name] = is_optional
            size_requirements[param.name] = required_size

    return input_events, input_event_mapping, parameter_optional_map, size_requirements
