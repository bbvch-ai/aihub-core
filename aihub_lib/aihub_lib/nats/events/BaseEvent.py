import json
import logging
import os
import threading
import time
from datetime import datetime
from functools import cache
from typing import Any, ClassVar, Dict, List, Optional, Type, Union

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field

logger = logging.getLogger(__name__)


def get_parent_classes_until_base(cls: Type, base_class: Type):
    """Returns a set of parent class names up until the given base class (excluding the base itself)."""
    parents = set()
    if cls.__name__ == base_class.__name__:
        return parents
    for base in cls.__bases__:
        if base is base_class:
            continue  # Stop at the given base class
        parents.add(base.__name__)
        parents.update(get_parent_classes_until_base(base, base_class))
    return parents


@cache
def get_inheritance_depth(event_class: Type, base_class: Type = None) -> int:
    """
    Calculate how many inheritance steps a class is from a base class.
    Higher values indicate more specific classes.
    """
    # Default to BaseEvent if no base_class specified
    if base_class is None:
        # This will be set to the BaseEvent class when used within BaseEvent
        base_class = BaseEvent

    if event_class == base_class:
        return 0

    depth = 0
    classes_to_check = [event_class]
    checked_classes = set()

    while classes_to_check:
        current_class = classes_to_check.pop(0)

        if current_class == base_class:
            return depth

        if current_class in checked_classes:
            continue

        checked_classes.add(current_class)

        # Add all base classes to check
        classes_to_check.extend(current_class.__bases__)
        depth += 1

    # If we get here, the class doesn't inherit from the base_class
    return -1


class BaseEvent(BaseModel):
    """
    The foundational event model from which all other event types inherit.
    It manages event type registration, dynamic deserialization, and stores common attributes
    like `event_id` and `created_at`.

    ### Why This Class Exists
    In a distributed event-driven system, different event types are emitted. By having a base
    event class, we can:
    - Standardize common fields (like event_id and created_at) across all events.
    - Maintain a registry of event subclasses to automatically deserialize events by their _type.
    - Provide utilities (like `to_trace_dict`) for consistent logging, tracing, and debugging.

    ### Key Features
    - **Automatic Registration:** Subclasses are registered upon definition. This allows `deserialize_event`
      to parse arbitrary event payloads and instantiate the correct subclass.
    - **Fallback for Unknown Types:** If the event’s `_type` is unknown, it defaults to a generic BaseEvent
      while preserving unknown fields.
    - **Trace-Friendly Output:** `to_trace_dict` converts timestamps and includes system-level info
      (PID, thread ID) for better observability in logs or traces.
    """

    _event_registry: ClassVar[Dict[str, Type["BaseEvent"]]] = {}
    event_id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: int = Field(
        default_factory=time.time_ns,
        description="The time (in ns since epoch) the event was stored in the event store",
    )

    # Private attributes to handle unknown event types
    _unknown_type: Optional[str] = PrivateAttr(None)
    _unknown_data: Optional[Dict[str, Any]] = PrivateAttr(None)
    _unknown_parent_classes: Optional[List[str]] = PrivateAttr(None)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    def __str__(self):
        return f"{self.__class__.__name__}({super().__str__()})"

    @computed_field
    @property
    def _type(self) -> str:
        """
        The event type name, usually the class name. If unknown, uses _unknown_type.
        Used during deserialization to decide which subclass to instantiate.
        """
        return self._unknown_type or self.__class__.__name__

    @computed_field
    @property
    def _parent_class_names(self) -> List[str]:
        """Contains the names of all parent classes up until BaseEvent."""
        if self._unknown_parent_classes is not None:
            return self._unknown_parent_classes
        return [self.__class__.__name__] + list(get_parent_classes_until_base(self.__class__, BaseEvent))

    @property
    def is_display_event(self) -> bool:
        return "DisplayEvent" in self._parent_class_names

    @property
    def is_control_event(self) -> bool:
        return "ControlEvent" in self._parent_class_names

    @property
    def is_exception_event(self) -> bool:
        return "ExceptionEvent" in self._parent_class_names

    @property
    def is_start_event(self) -> bool:
        return "StartEvent" in self._parent_class_names

    @property
    def is_stop_event(self) -> bool:
        return "StopEvent" in self._parent_class_names

    @property
    def is_user_message_event(self) -> bool:
        return "UserMessageEvent" in self._parent_class_names

    @property
    def is_semantic_event(self) -> bool:
        return "SemanticEvent" in self._parent_class_names

    @property
    def is_hitl_request_event(self) -> bool:
        return "HumanInTheLoopRequestEvent" in self._parent_class_names

    @property
    def is_hitl_response_event(self) -> bool:
        return "HumanInTheLoopResponseEvent" in self._parent_class_names

    @property
    def is_aitl_request_event(self) -> bool:
        return "AgentInTheLoopRequestEvent" in self._parent_class_names

    @property
    def is_aitl_response_event(self) -> bool:
        return "AgentInTheLoopResponseEvent" in self._parent_class_names

    @property
    def is_aitl_exception_event(self) -> bool:
        return "AgentInTheLoopExceptionEvent" in self._parent_class_names

    @property
    def is_chunk_event(self) -> bool:
        return "ChunkEvent" in self._parent_class_names

    @property
    def is_thought_event(self) -> bool:
        return "ThoughtEvent" in self._parent_class_names

    @property
    def is_llm_cost_event(self) -> bool:
        return "LLMCostEvent" in self._parent_class_names

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Called when a new subclass is defined, registering it in the _event_registry.
        This makes dynamic deserialization possible.
        """
        super().__pydantic_init_subclass__(**kwargs)
        logger.debug(f"Registering Event {cls.__name__}")
        if cls.__name__ in BaseEvent._event_registry:
            raise ValueError(f"Duplication detected for Event {cls.__name__}")
        BaseEvent._event_registry[cls.__name__] = cls

    @classmethod
    def deserialize_event(cls, data: Union[bytes, str, Dict[str, Any]]) -> "BaseEvent":
        """
        Given raw event data, deserializes it into the most specific event class possible
        based on inheritance hierarchy, while preserving original type information.
        """
        if isinstance(data, dict):
            json_data = data.copy()
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        # First, process any nested events recursively
        for key, value in list(json_data.items()):
            if isinstance(value, dict) and "_type" in value:
                json_data[key] = cls.deserialize_event(value)

        # Get event type and parent classes
        event_type = json_data.get("_type")
        parent_classes = json_data.get("_parent_class_names", [])

        # If the exact class is registered, try to instantiate it and propagate any validation errors
        if event_type and isinstance(event_type, str):
            event_class = cls._event_registry.get(event_type)
            if event_class:
                # For known event types, we should not catch validation errors
                # This ensures validation failures propagate to the caller
                return event_class(**json_data)

        # If we get here, either:
        # 1. The event type wasn't in our registry, or
        # 2. The event type was null/invalid

        # Try to find the most specific parent class
        candidates = []
        if parent_classes and isinstance(parent_classes, list):
            for class_name, event_class in cls._event_registry.items():
                # Check if this class is in the parent classes list
                if class_name in parent_classes:
                    # Get inheritance depth (higher means more specific)
                    depth = get_inheritance_depth(event_class, BaseEvent)
                    if depth >= 0:  # Only consider classes that inherit from BaseEvent
                        candidates.append((event_class, depth))

        # Sort candidates by depth (most specific/deepest first)
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Try to instantiate candidates in order of specificity
        for candidate_class, depth in candidates:
            try:
                # Create the instance with the parent class
                event = candidate_class(**json_data)

                # Set the private attributes since this isn't the exact original class
                event._unknown_type = event_type
                event._unknown_data = json_data
                event._unknown_parent_classes = parent_classes

                logger.warning(f"{event_type} not found in registry. Using closest parent {candidate_class.__name__}.")

                return event
            except Exception as e:
                logger.warning(f"Failed to create {candidate_class.__name__} instance: {e}. Trying next candidate.")

        # If all else fails, fall back to BaseEvent
        logger.warning(f"{event_type} not found in registry. Using fallback {cls.__name__}.")

        event = cls(**json_data)

        # Set private attributes for BaseEvent fallback
        event._unknown_type = event_type
        event._unknown_data = json_data
        event._unknown_parent_classes = parent_classes

        return event

    def to_trace_dict(self) -> Dict[str, Any]:
        """
        Prepares a dictionary suitable for tracing and logging:
        - Human-readable timestamps.
        - Process and thread identifiers.
        This aids in debugging complex event flows.
        """
        event_dict = {
            **self.model_dump(),
            "os_pid": os.getpid(),
            "os_threadid": threading.get_ident(),
        }
        created_at = event_dict["created_at"]

        # Convert ns timestamp to a readable datetime
        created_datetime = datetime.fromtimestamp(created_at / 1_000_000_000)
        event_dict["created_at"] = created_datetime.strftime("%Y-%m-%d %H:%M:%S.%f") + f"{created_at % 1_000:03d}"
        return event_dict

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Serializes the event into a dictionary. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        data = super().model_dump(**kwargs)
        for field_name, value in self.__dict__.items():
            if isinstance(value, BaseEvent):
                data[field_name] = value.model_dump()

        if not self._unknown_data:
            return data

        return {
            **self._unknown_data,
            **data,
        }
