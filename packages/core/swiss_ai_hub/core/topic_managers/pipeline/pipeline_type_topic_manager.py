from typing import Annotated, override

from pydantic import Field, field_validator

from swiss_ai_hub.core.topic_managers.abstract_stream_topic_manager import AbstractStreamTopicManager
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types import PipelineSourceType, PipelineTargetType
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_topic_manager import PipelineTopicManager
from swiss_ai_hub.core.topics.pipeline.pipeline_topic import PipelineTopic


class PipelineTypeTopicManager(PipelineTopicManager, AbstractStreamTopicManager):
    """Routes a configurable pipeline's events on a subject keyed by ingestor rather than by bucket.

    A per-bucket subject forces one JetStream stream and consumer per knowledge database, so streams,
    consumers and per-tick polls all grow with the number of databases. Keying the subject on the
    ingestor instead gives each deployed pipeline exactly one stream and one consumer regardless of how
    many databases it owns; the bucket travels in the subject's source-id token, which the sensor reads
    back to group a drained batch by database.
    """

    pipeline_type: Annotated[str, Field(description="Ingestor id owning the pipeline, such as 'rag'")]

    @field_validator("pipeline_type")
    @classmethod
    def _reject_reserved_or_wildcard(cls, value: str) -> str:
        if value in tuple(PipelineSourceType):
            msg = (
                f"'{value}' is reserved for the legacy per-instance subject grammar; a stream filtered on "
                f"'pipeline.{value}.>' would overlap the legacy streams, which JetStream forbids."
            )
            raise ValueError(msg)
        if not value or any(character in value for character in ".*> "):
            msg = f"'{value}' is not a usable NATS subject token."
            raise ValueError(msg)
        return value

    def get_subject_for_source_updated(
        self,
        bucket_name: Annotated[str, "Data lake bucket the uploaded document landed in"],
        db_name: Annotated[str, "Knowledge database the bucket feeds"],
        run_key: Annotated[str, "Pipeline run key"],
        event_name: Annotated[str, "Specific event name"],
        event_id: Annotated[str, "Event instance ID"],
    ) -> str:
        return self.get_subject_for_specific_event_in_pipeline(
            source_type=self.pipeline_type,
            source_id=bucket_name,
            target_type=PipelineTargetType.KNOWLEDGE,
            target_id=db_name,
            run_key=run_key,
            event_name=event_name,
            event_id=event_id,
        )

    @staticmethod
    def bucket_from_subject(subject: Annotated[str, "Subject a consumed message arrived on"]) -> str:
        """Bucket a message belongs to, so the sensor never needs to know the subject grammar itself."""
        return PipelineTopic.from_subject(subject).source_id

    @override
    def get_stream(self) -> tuple[str, str]:
        return f"{self.PIPELINE_TOPIC}_{self.pipeline_type}_stream", f"{self.PIPELINE_TOPIC}.{self.pipeline_type}.>"

    @override
    def get_subject_for_all_control_events(self) -> str:
        return f"{self.PIPELINE_TOPIC}.{self.pipeline_type}.>"
