from enum import Enum


class MemoryEventType(str, Enum):
    """Event types for memory operations."""

    ADD = "ADD"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    NONE = "NONE"
