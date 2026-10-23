from enum import StrEnum


class VersionMatchOutcome(StrEnum):
    """What a chat message says about the release it asks for."""

    FOUND = "found"
    SEVERAL = "several"
    UNKNOWN = "unknown"
    MISSING = "missing"
