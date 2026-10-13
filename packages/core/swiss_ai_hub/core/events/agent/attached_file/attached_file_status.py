from enum import StrEnum


class AttachedFileStatus(StrEnum):
    """How much of an attached file reached the model."""

    READ = "read"
    TRUNCATED = "truncated"
    FAILED = "failed"
