import inspect
from types import UnionType
from typing import Annotated, Any, List, Optional, Set, Tuple, Type, Union, get_args, get_origin

from aihub_lib.nats.events import BaseEvent


def extract_event_types(
    annotation: Annotated[Any, "A type annotation representing one or more event types."],
) -> Tuple[Set[Type[BaseEvent]], bool, Optional[int]]:
    """
    Analyze a type annotation related to events and extract:
    - The set of possible event types (classes inheriting from BaseEvent).
    - Whether the annotation allows None (i.e., is optional).
    - A required size, if defined (e.g., for fixed-size collections).

    This function helps determine what kinds of events a workflow step method can accept or produce,
    as well as any constraints on those events (like required size).

    ### Parameters
    - `annotation` (Any): A type annotation that could reference:
      - A single BaseEvent subclass
      - A Union of multiple BaseEvent subclasses
      - Optional types (BaseEvent | None)
      - Containers like List[SomeEvent] or a fixed-size list type.

    ### Returns
    A tuple `(event_types, is_optional, required_size)` where:
    - `event_types`: A set of BaseEvent subclasses extracted from the annotation.
    - `is_optional`: A boolean indicating if `None` is allowed.
    - `required_size`: An integer if a fixed size is required, otherwise None.

    ### How It Works
    1. **Fixed-size Containers:**
       If `annotation` has a `_required_size` attribute, we treat it as a fixed-size container of events.

    2. **Union/Optional:**
       If the annotation is a Union or UnionType and includes `None`, we mark it as optional.
       We recursively process the non-None arguments to gather event types.

    3. **Containers (List[SomeEvent]):**
       If the annotation is a list-like, we recurse into its element type.

    4. **Direct Event Type:**
       If the annotation directly references a BaseEvent subclass, we add it to the `event_types`.

    ### Examples
    - `SomeEvent` → event_types={SomeEvent}, is_optional=False, required_size=None
    - `SomeEvent | None` → event_types={SomeEvent}, is_optional=True, required_size=None
    - `List[SomeEvent]` → event_types={SomeEvent}, is_optional=False, required_size=None
    - `FixedList[AnotherEvent, 3]` (hypothetical) → event_types={AnotherEvent}, is_optional=False, required_size=3
    """

    event_types: Set[Type[BaseEvent]] = set()
    is_optional = False
    required_size = None
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Check if annotation has a _required_size attribute indicating a fixed-size container.
    if hasattr(annotation, "_required_size"):
        required_size = annotation._required_size
        # Extract the event type from the generic base of this annotation
        base_type = annotation.__orig_bases__[0].__args__[0]  # type: ignore
        if inspect.isclass(base_type) and issubclass(base_type, BaseEvent):
            event_types.add(base_type)

    elif origin in (Union, UnionType):
        # Handling Union / Optional types
        if type(None) in args:
            # It's something like: SomeEvent | None
            is_optional = True
            non_none_args = [arg for arg in args if arg is not type(None)]
            for arg in non_none_args:
                etypes, _, _ = extract_event_types(arg)
                event_types.update(etypes)
        else:
            # A union without None, e.g. SomeEvent | AnotherEvent
            for arg in args:
                etypes, _, _ = extract_event_types(arg)
                event_types.update(etypes)

    elif origin in (list, List):
        # List[...] of events
        elem_type = args[0]
        etypes, optional, _ = extract_event_types(elem_type)
        event_types.update(etypes)
        is_optional = optional

    elif inspect.isclass(annotation) and issubclass(annotation, BaseEvent):
        # Direct event class
        event_types.add(annotation)

    return event_types, is_optional, required_size
