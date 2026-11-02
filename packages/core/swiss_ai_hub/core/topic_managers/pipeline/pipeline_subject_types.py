from enum import StrEnum


class PipelineSourceType(StrEnum):
    """Source token of a pipeline NATS subject.

    Owned by core because the API publishes the subject and the pipeline consumes it; a drift of one
    character between the two would silently route events to a subject nobody polls.
    """

    DATALAKE = "datalake"


class PipelineTargetType(StrEnum):
    """Target token of a pipeline NATS subject. See ``PipelineSourceType`` for why it lives in core."""

    KNOWLEDGE = "knowledge"
