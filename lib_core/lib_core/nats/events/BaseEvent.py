import logging
import os
import threading
import time
from datetime import datetime
from typing import Type, ClassVar, Dict, Optional, Any, Union

import json
from bson import ObjectId
from pydantic import BaseModel, Field, computed_field, ConfigDict, PrivateAttr

logger = logging.getLogger(__name__)


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

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    @computed_field  # makes _type a computed property
    @property
    def _type(self) -> str:
        """
        The event type name, usually the class name. If unknown, uses _unknown_type.
        Used during deserialization to decide which subclass to instantiate.
        """
        return self._unknown_type or self.__class__.__name__

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Called when a new subclass is defined, registering it in the _event_registry.
        This makes dynamic deserialization possible.
        """
        super().__pydantic_init_subclass__(**kwargs)
        logger.debug(f"Registering Event {cls.__name__}")
        BaseEvent._event_registry[cls.__name__] = cls

    @classmethod
    def deserialize_event(cls, data: Union[bytes, str, Dict[str, Any]]) -> "BaseEvent":
        """
        Given raw event data (JSON string, bytes, or dict), attempts to:
        1. Parse it into a dictionary.
        2. Identify the event type (_type).
        3. Instantiate the corresponding event class, falling back to BaseEvent if unknown.

        This lets you handle arbitrary events from the wire without manually selecting the event class.
        """
        if isinstance(data, dict):
            json_data = data
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        event_type = json_data.get("_type")
        if event_type and isinstance(event_type, str):
            event_class = cls._event_registry.get(event_type)
            if event_class:
                return event_class(**json_data)

        logger.warning(
            f"Unknown event type: {event_type}. Using BaseEvent. Known types: {list(BaseEvent._event_registry.keys())}"
        )
        return cls(_unknown_type=event_type, **json_data, _unknown_data=json_data)

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
        if not self._unknown_data:
            return data
        return {
            **self._unknown_data,
            **data,
        }
