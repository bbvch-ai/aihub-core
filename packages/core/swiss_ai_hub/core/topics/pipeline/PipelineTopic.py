from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.topic_managers.pipeline.PipelineTopicManager import PipelineTopicManager
from swiss_ai_hub.core.topics import Topic


class PipelineTopic(Topic):
    """
    Structured representation of pipeline event subjects, encoding data flow metadata within NATS topics.

    Captures the complete context of a pipeline event including source and target systems, run identifiers,
    and specific event information. Provides bidirectional conversion between structured topic objects and
    NATS subject strings, enabling type-safe topic handling while maintaining compatibility with NATS
    wildcard subscriptions for monitoring and debugging workflows.
    """

    source_type: Annotated[str, "Pipeline source type, such as 'datalake'"]
    source_id: Annotated[str, "Pipeline source id / container name"]
    target_type: Annotated[str, "Pipeline target type, such as 'knowledge'"]
    target_id: Annotated[str, "Pipeline target id / knowledge db name"]
    run_key: Annotated[str, "Run key used by dagster to prevent duplicated runs"]
    event_name: Annotated[str | None, Field(description="Event name or None if unspecified.")] = None
    event_id: Annotated[str | None, Field(description="Event ID or None if unspecified.")] = None

    def execution_context_id(self) -> str:
        return self.run_key

    def __str__(self) -> str:
        """Returns the full subject string for this pipeline topic."""
        return (
            f"{PipelineTopicManager.PIPELINE_TOPIC}."
            f"{self.source_type}."
            f"{self.source_id}."
            f"to."
            f"{self.target_type}."
            f"{self.target_id}."
            f"{self.run_key}."
            f"{self.event_name}."
            f"{self.event_id}"
        )

    @classmethod
    def from_subject(cls, subject: str) -> Self:
        (
            topic_type,
            source_type,
            source_id,
            _to,
            target_type,
            target_id,
            run_key,
            event_name,
            event_id,
        ) = subject.split(".")
        assert topic_type == PipelineTopicManager.PIPELINE_TOPIC, f"Unexpected topic type in subject: {subject}"
        if _to != "to":
            raise ValueError(f"Unexpected subject format: {subject}")
        return cls(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            run_key=run_key,
            event_name=event_name,
            event_id=event_id,
        )
