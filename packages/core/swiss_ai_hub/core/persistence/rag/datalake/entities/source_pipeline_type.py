from enum import StrEnum


class SourcePipelineType(StrEnum):
    """The platform's own routing tokens for which deployed source pipeline fills a knowledge database.

    A database with no source is filled by manual upload, which is why ``BucketEntity.source`` has no default
    token: absence is the manual case. ``rclone`` is the shipped source pipeline; like the shipped ingestor it
    registers itself, so the API learns about it from its registration record rather than from this enum.
    """

    RCLONE = "rclone"
