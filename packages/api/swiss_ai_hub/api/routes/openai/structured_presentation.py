from enum import StrEnum


class StructuredPresentation(StrEnum):
    """How the caller asked for the JSON, and so how it gets it back: as the message content or as a tool call."""

    CONTENT = "content"
    TOOL_CALL = "tool_call"
