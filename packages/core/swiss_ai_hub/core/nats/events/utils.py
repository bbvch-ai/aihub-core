from functools import cache
from typing import TYPE_CHECKING, Annotated, Union, get_args, get_origin

from swiss_ai_hub.core.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize

if TYPE_CHECKING:
    from swiss_ai_hub.core.nats.events.BaseEvent import BaseEvent


def get_parent_classes_until_base(cls: type, base_class: type):
    """Returns a set of parent class names up until the given base class (excluding the base itself)."""
    if cls is base_class:
        return set()

    if base_class not in cls.__mro__:
        # If base_class is not in the hierarchy, collect all parents except 'object'
        return {base.__name__ for base in cls.__mro__[1:] if base is not object}

    base_idx = cls.__mro__.index(base_class)

    parent_names = {c.__name__ for c in cls.__mro__[1:base_idx] if c is not object}

    return parent_names


@cache
def get_inheritance_depth(event_class: type, base_class: type = None) -> int:
    """
    Calculate the maximum inheritance depth from a class to a base class.
    Returns the longest path in case of multiple inheritance paths.
    """
    # Default to BaseEvent if no base_class specified
    if base_class is None:
        base_class = BaseEvent

    # Base case: if we've reached the base class
    if event_class == base_class:
        return 0

    # If no base classes, we can't go further
    if not event_class.__bases__:
        return -1

    # Find the maximum depth by checking all base classes
    max_depth = -1
    for parent_class in event_class.__bases__:
        parent_depth = get_inheritance_depth(parent_class, base_class)
        # Only consider valid paths (depth >= 0)
        if parent_depth >= 0:
            max_depth = max(max_depth, parent_depth + 1)

    return max_depth


def get_base_type(annotation: type) -> tuple[type, ...]:
    """
    Recursively unwraps a type hint to find the core, non-wrapper type(s).
    """
    origin = get_origin(annotation)

    # Case 1: Annotated[T, ...]
    if origin is Annotated:
        return get_base_type(get_args(annotation)[0])

    # Case 2: Union[A, B, ...] or Optional[A] or A | None
    if origin is Union:
        base_types: list[type] = []
        for arg in get_args(annotation):
            if arg is not type(None):
                base_types.extend(get_base_type(arg))
        return tuple(base_types)

    # Case 3: list[T] or a custom generic like ListOfSize[T, ...]
    is_list_like = isinstance(origin, type) and issubclass(origin, list)
    if origin is list or origin is ListOfSize or is_list_like:
        return get_base_type(get_args(annotation)[0])

    if isinstance(annotation, type):
        return (annotation,)

    return (annotation,)
