from enum import StrEnum


class SourcePipelineType(StrEnum):
    """The platform's own routing tokens for which deployed source pipeline fills a knowledge database.

    A database with no source is filled by manual upload, which is why ``BucketEntity.source`` has no default
    token: absence is the manual case. ``rclone`` syncs files and ``structured`` syncs API records as markdown;
    like the shipped ingestor each registers itself, so the API learns about it from its registration record rather
    than from this enum.
    """

    RCLONE = "rclone"
    STRUCTURED = "structured"
