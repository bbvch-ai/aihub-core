from functools import cache
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from aihub_lib.nats.events.BaseEvent import BaseEvent


def get_parent_classes_until_base(cls: Type, base_class: Type):
    """Returns a set of parent class names up until the given base class (excluding the base itself)."""
    if cls is base_class:
        return set()

    # Check if base_class is in the MRO (Method Resolution Order) of cls
    if base_class not in cls.__mro__:
        # If base_class is not in the hierarchy, collect all parents except 'object'
        return {base.__name__ for base in cls.__mro__[1:] if base is not object}

    # Get position of base_class in MRO
    base_idx = cls.__mro__.index(base_class)

    # Collect all class names between cls and base_class in the MRO, excluding 'object'
    parent_names = {c.__name__ for c in cls.__mro__[1:base_idx] if c is not object}

    return parent_names


@cache
def get_inheritance_depth(event_class: Type, base_class: Type = None) -> int:
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
