from enum import StrEnum


class MemoryEventType(StrEnum):
    """Event types for memory operations."""

    ADD = "ADD"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    NONE = "NONE"
