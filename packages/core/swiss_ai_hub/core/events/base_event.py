import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, ClassVar, Self, override

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field

from swiss_ai_hub.core.events.utils import get_inheritance_depth, get_parent_classes_until_base

logger = logging.getLogger(__name__)


def serialize_chat_message_blocks(chat_message: ChatMessage, **kwargs: Any) -> dict:
    msg_dict = chat_message.model_dump(**kwargs)
    for block in msg_dict["blocks"]:
        if block["block_type"] in ["audio", "image"] and block.get("url") is not None:
            block["url"] = str(block["url"])
            if block.get("path") is not None:
                block["path"] = str(block["path"])

    return msg_dict


class BaseEvent(BaseModel):
    """
    The foundational event model from which all other event types inherit.
    It manages event type registration, dynamic deserialization, and stores common attributes
    like `event_id` and `created_at`.

    ### Why This Class Exists
    In a distributed event-driven system, different event types are emitted. By having a base
    event class, we can:
    - Standardize common fields (like event_id and created_at) across all events.
    - Maintain a registry of event subclasses to automatically deserialize events by their _event_name.
    - Provide utilities (like `to_trace_dict`) for consistent logging, tracing, and debugging.

    ### Key Features
    - **Automatic Registration:** Subclasses are registered upon definition. This allows `deserialize_event`
      to parse arbitrary event payloads and instantiate the correct subclass.
    - **Fallback for Unknown Types:** If the event’s `_event_name` is unknown, it defaults to a generic BaseEvent
      while preserving unknown fields.
    - **Trace-Friendly Output:** `to_trace_dict` converts timestamps and includes system-level info
      (PID, thread ID) for better observability in logs or traces.
    """

    _event_registry: ClassVar[dict[str, type["BaseEvent"]]] = {}
    event_id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: int = Field(
        default_factory=time.time_ns,
        description="The time (in ns since epoch) the event was stored in the event store",
    )

    # Private attributes to handle unknown event types
    _unknown_event_name: str | None = PrivateAttr(None)
    _unknown_data: dict[str, Any] | None = PrivateAttr(None)
    _unknown_parent_classes: list[str] | None = PrivateAttr(None)

    _jetstream_sequence: int | None = PrivateAttr(None)

    # X-AIHub-* headers from the NATS message that delivered this event. Set by the subscribers
    # per delivery — not serialized, not durable across JetStream replay. May include tokens.
    # Untrusted client input: a consumer must validate a value before acting on it (e.g. as an
    # identity claim) — see NATSMessageHeaders.AIHUB_HEADER_PREFIX.
    _aihub_headers: dict[str, str] | None = PrivateAttr(None)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    def __str__(self):
        return f"{self.event_name}({super().__str__()})"

    @property
    def sequence_number(self):
        if self._jetstream_sequence is None:
            raise ValueError("Sequence number is not set for this event.")
        return self._jetstream_sequence

    @computed_field
    @property
    def _event_name(self) -> str:
        """
        The event type name, usually the class name. If unknown, uses _unknown_event_name.
        Used during deserialization to decide which subclass to instantiate.
        """
        return self._unknown_event_name or self.__class__.__name__

    @classmethod
    def event_name_from_class(cls):
        return cls.__name__

    @property
    def event_name(self):
        return self._event_name

    @classmethod
    def parent_event_names_from_class(cls) -> list[str]:
        result = [cls.event_name_from_class()]
        parent_classes = get_parent_classes_until_base(cls, BaseEvent)
        class_dict = {cls.__name__: cls for cls in cls.__mro__ if cls.__name__ in parent_classes}
        sorted_parent_classes = sorted(
            parent_classes, key=lambda name: get_inheritance_depth(class_dict[name], BaseEvent), reverse=True
        )

        result.extend(sorted_parent_classes)
        return result

    @computed_field
    @property
    def _parent_event_names(self) -> list[str]:
        """
        Contains the names of all parent classes up until BaseEvent, ordered from deepest to least deep inheritance.
        """
        if self._unknown_parent_classes is not None:
            return self._unknown_parent_classes

        result = [self.event_name]
        parent_classes = get_parent_classes_until_base(self.__class__, BaseEvent)
        class_dict = {cls.__name__: cls for cls in self.__class__.__mro__ if cls.__name__ in parent_classes}
        sorted_parent_classes = sorted(
            parent_classes, key=lambda name: get_inheritance_depth(class_dict[name], BaseEvent), reverse=True
        )

        result.extend(sorted_parent_classes)
        return result

    @property
    def is_display_event(self) -> bool:
        return "DisplayEvent" in self._parent_event_names

    @property
    def is_control_event(self) -> bool:
        return "ControlEvent" in self._parent_event_names

    @property
    def is_process_event(self) -> bool:
        return "ProcessEvent" in self._parent_event_names

    @property
    def is_process_start_event(self) -> bool:
        return "ProcessStartEvent" in self._parent_event_names

    @property
    def is_process_stop_event(self) -> bool:
        return "ProcessStopEvent" in self._parent_event_names

    @property
    def is_process_exception_event(self) -> bool:
        return "ProcessExceptionEvent" in self._parent_event_names

    @property
    def is_work_event(self) -> bool:
        return "WorkEvent" in self._parent_event_names

    @property
    def is_work_request_event(self) -> bool:
        return "WorkRequestEvent" in self._parent_event_names

    @property
    def is_human_work_event(self) -> bool:
        return "HumanWorkEvent" in self._parent_event_names

    @property
    def is_program_work_event(self) -> bool:
        return "ProgramWorkEvent" in self._parent_event_names

    @property
    def is_exception_event(self) -> bool:
        return "ExceptionEvent" in self._parent_event_names

    @property
    def is_start_event(self) -> bool:
        return "StartEvent" in self._parent_event_names

    @property
    def is_stop_event(self) -> bool:
        return "StopEvent" in self._parent_event_names

    @property
    def is_user_message_event(self) -> bool:
        return "UserMessageEvent" in self._parent_event_names

    @property
    def is_semantic_event(self) -> bool:
        return "SemanticEvent" in self._parent_event_names

    @property
    def is_hitl_request_event(self) -> bool:
        return "HumanInTheLoopRequestEvent" in self._parent_event_names

    @property
    def is_hitl_response_event(self) -> bool:
        return "HumanInTheLoopResponseEvent" in self._parent_event_names

    @property
    def is_aitl_request_event(self) -> bool:
        return "AgentInTheLoopRequestEvent" in self._parent_event_names

    @property
    def is_aitl_response_event(self) -> bool:
        return "AgentInTheLoopResponseEvent" in self._parent_event_names

    @property
    def is_aitl_exception_event(self) -> bool:
        return "AgentInTheLoopExceptionEvent" in self._parent_event_names

    @property
    def is_bitl_request_event(self) -> bool:
        return "BotInTheLoopRequestEvent" in self._parent_event_names

    @property
    def is_bitl_response_event(self) -> bool:
        return "BotInTheLoopResponseEvent" in self._parent_event_names

    @property
    def is_chunk_event(self) -> bool:
        return "ChunkEvent" in self._parent_event_names

    @property
    def is_thought_event(self) -> bool:
        return "ThoughtEvent" in self._parent_event_names

    @property
    def is_llm_cost_event(self) -> bool:
        return "LLMCostEvent" in self._parent_event_names

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
    def deserialize_event(
        cls,
        data: bytes | str | dict[str, Any],
    ) -> Self:
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
            if isinstance(value, dict) and "_event_name" in value:
                json_data[key] = cls.deserialize_event(value)
            elif isinstance(value, list):
                json_data[key] = [
                    cls.deserialize_event(item) if isinstance(item, dict) and "_event_name" in item else item
                    for item in value
                ]

        event_name: str = json_data.get("_event_name")
        parent_classes: list[str] = json_data.get("_parent_event_names", [])

        # If the exact class is registered, try to instantiate it and propagate any validation errors
        if event_name and isinstance(event_name, str):
            event_class = cls._event_registry.get(event_name)
            if event_class:
                return event_class.model_validate(json_data)

        # If we get here, either:
        # 1. The event type wasn't in our registry, or
        # 2. The event type was null/invalid

        # Try to find the most specific parent class
        if parent_classes and isinstance(parent_classes, list):
            for class_name in parent_classes:
                event_class = cls._event_registry.get(class_name)
                if event_class:
                    try:
                        # Special case handling for control and display events
                        if event_class.__name__ == "ControlEvent" and "DisplayEvent" in parent_classes:
                            event_class = cls._event_registry.get("ControlAndDisplayEvent")

                        if event_class.__name__ == "DisplayEvent" and "ControlEvent" in parent_classes:
                            event_class = cls._event_registry.get("ControlAndDisplayEvent")

                        event = event_class.model_validate(json_data)

                        event._unknown_event_name = event_name
                        event._unknown_data = json_data
                        event._unknown_parent_classes = parent_classes

                        logger.warning(
                            f"{event_name} not found in registry. Using closest parent {event_class.__name__}."
                        )

                        return event
                    except Exception as e:
                        logger.warning(f"Failed to create {event_class.__name__} instance: {e}. Trying next candidate.")

        # If all else fails, fall back to BaseEvent
        logger.warning(f"{event_name} not found in registry. Using fallback {cls.__name__}.")

        event = cls.model_validate(json_data)

        event._unknown_event_name = event_name
        event._unknown_data = json_data
        event._unknown_parent_classes = parent_classes

        return event

    def to_trace_dict(self) -> dict[str, Any]:
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

        created_datetime = datetime.fromtimestamp(created_at / 1e9)
        event_dict["created_at"] = created_datetime.strftime("%Y-%m-%d %H:%M:%S.%f") + f"{created_at % 1_000:03d}"
        return event_dict

    @override
    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        Serializes the event into a dictionary. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        kwargs["serialize_as_any"] = True

        data = super().model_dump(**kwargs)

        for field_name in self.__class__.model_fields.keys():
            if field_name in data:
                value = getattr(self, field_name)
                if isinstance(value, ChatMessage):
                    data[field_name] = serialize_chat_message_blocks(value, **kwargs)
                elif isinstance(value, BaseModel):
                    data[field_name] = value.model_dump(**kwargs)
                elif isinstance(value, list | tuple):
                    data[field_name] = [self._item_dump(item, **kwargs) for item in value]

        if not self._unknown_data:
            return data

        return {
            **self._unknown_data,
            **data,
        }

    @staticmethod
    def _item_dump(item: Any, **kwargs: Any):
        if isinstance(item, ChatMessage):
            return serialize_chat_message_blocks(item, **kwargs)
        elif isinstance(item, BaseModel):
            return item.model_dump(**kwargs)
        else:
            return item

    @override
    def model_dump_json(self, **kwargs: Any) -> str:
        """
        Serializes the event into a JSON string. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        return json.dumps(self.model_dump(**kwargs), default=str)
