import inspect
from types import UnionType
from typing import Annotated, Any, Union, get_args, get_origin

from aihub_lib.nats.events import BaseEvent


def extract_event_classes(
    annotation: Annotated[Any, "A type annotation representing one or more event types."],
) -> tuple[set[type[BaseEvent]], bool, int | None]:
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
      - Containers like list[SomeEvent] or a fixed-size list type.

    ### Returns
    A tuple `(event_classes, is_optional, required_size)` where:
    - `event_classes`: A set of BaseEvent subclasses extracted from the annotation.
    - `is_optional`: A boolean indicating if `None` is allowed.
    - `required_size`: An integer if a fixed size is required, otherwise None.

    ### How It Works
    1. **Fixed-size Containers:**
       If `annotation` has a `_required_size` attribute, we treat it as a fixed-size container of events.

    2. **Union/Optional:**
       If the annotation is a Union or UnionType and includes `None`, we mark it as optional.
       We recursively process the non-None arguments to gather event types.

    3. **Containers (list[SomeEvent]):**
       If the annotation is a list-like, we recurse into its element type.

    4. **Direct Event Type:**
       If the annotation directly references a BaseEvent subclass, we add it to the `event_classes`.

    ### Examples
    - `SomeEvent` → event_classes={SomeEvent}, is_optional=False, required_size=None
    - `SomeEvent | None` → event_classes={SomeEvent}, is_optional=True, required_size=None
    - `list[SomeEvent]` → event_classes={SomeEvent}, is_optional=False, required_size=None
    - `Fixedlist[AnotherEvent, 3]` (hypothetical) → event_classes={AnotherEvent}, is_optional=False, required_size=3
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Handle Annotated wrapper
    if origin is Annotated:
        return extract_event_classes(args[0])

    # Process the annotation based on its type
    return _process_annotation(annotation, origin, args)


def _process_annotation(
    annotation: Any, origin: Any, args: tuple[Any, ...]
) -> tuple[set[type[BaseEvent]], bool, int | None]:
    """Process different types of annotations to extract event information."""
    event_classes: set[type[BaseEvent]] = set()
    is_optional = False
    required_size = None

    if hasattr(annotation, "_required_size"):
        return _handle_fixed_size_container(annotation)
    elif origin in (Union, UnionType):
        return _handle_union_type(args)
    elif origin in (list, list):
        return _handle_list_type(args)
    elif _is_direct_event_class(annotation):
        event_classes.add(annotation)

    return event_classes, is_optional, required_size


def _handle_fixed_size_container(annotation: Any) -> tuple[set[type[BaseEvent]], bool, int | None]:
    """Handle fixed-size container annotations."""
    event_classes: set[type[BaseEvent]] = set()
    required_size = annotation._required_size
    base_type = annotation._item_type  # type: ignore
    
    if inspect.isclass(base_type) and issubclass(base_type, BaseEvent):
        event_classes.add(base_type)
    
    return event_classes, False, required_size


def _handle_union_type(args: tuple[Any, ...]) -> tuple[set[type[BaseEvent]], bool, int | None]:
    """Handle Union and UnionType annotations."""
    event_classes: set[type[BaseEvent]] = set()
    is_optional = type(None) in args
    
    # Filter out None types and process remaining arguments
    relevant_args = [arg for arg in args if arg is not type(None)]
    for arg in relevant_args:
        etypes, _, _ = extract_event_classes(arg)
        event_classes.update(etypes)
    
    return event_classes, is_optional, None


def _handle_list_type(args: tuple[Any, ...]) -> tuple[set[type[BaseEvent]], bool, int | None]:
    """Handle list type annotations."""
    if not args:
        return set(), False, None
        
    elem_type = args[0]
    etypes, is_optional, _ = extract_event_classes(elem_type)
    return etypes, is_optional, None


def _is_direct_event_class(annotation: Any) -> bool:
    """Check if annotation is a direct BaseEvent subclass."""
    return inspect.isclass(annotation) and issubclass(annotation, BaseEvent)
