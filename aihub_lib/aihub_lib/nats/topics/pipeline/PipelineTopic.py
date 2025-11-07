from typing import Annotated

from pydantic import Field

from aihub_lib.nats.topic_managers.pipeline.PipelineTopicManager import PipelineTopicManager
from aihub_lib.nats.topics import Topic


class PipelineTopic(Topic):
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
    def from_subject(cls, subject: str) -> "PipelineTopic":
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
