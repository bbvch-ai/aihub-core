from types import UnionType
from typing import Any, Type, Set, Union, get_origin, get_args, Tuple, List, Optional
import inspect

from lib_core.nats.events import BaseEvent


def extract_event_types(annotation: Any) -> Tuple[Set[Type[BaseEvent]], bool, Optional[int]]:
    """
    Extracts event types from a type annotation.
    Returns a tuple of (event_types, is_optional).
    """
    event_types = set()
    is_optional = False
    required_size = None
    origin = get_origin(annotation)
    args = get_args(annotation)

    if hasattr(annotation, '_required_size'):
        required_size = annotation._required_size
        base_type = annotation.__orig_bases__[0].__args__[0]
        if inspect.isclass(base_type) and issubclass(base_type, BaseEvent):
            event_types.add(base_type)
    elif origin in (Union, UnionType):
        if type(None) in args:
            is_optional = True
            non_none_args = [arg for arg in args if arg is not type(None)]
            for arg in non_none_args:
                etypes, _, _ = extract_event_types(arg)
                event_types.update(etypes)
        else:
            for arg in args:
                etypes, _, _ = extract_event_types(arg)
                event_types.update(etypes)
    elif origin in (list, List):
        elem_type = args[0]
        etypes, optional, _ = extract_event_types(elem_type)
        event_types.update(etypes)
        is_optional = optional
    elif inspect.isclass(annotation) and issubclass(annotation, BaseEvent):
        event_types.add(annotation)

    return event_types, is_optional, required_size