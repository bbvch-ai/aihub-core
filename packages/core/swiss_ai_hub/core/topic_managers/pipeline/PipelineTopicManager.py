from typing import Annotated, ClassVar

from swiss_ai_hub.core.topic_managers.TopicManager import TopicManager


class PipelineTopicManager(TopicManager):
    """
    Manages NATS subject patterns for pipeline-related events and discovery operations.

    Provides standardized subject naming conventions for pipeline events flowing between data sources
    and targets (e.g., datalake to knowledge database). This ensures consistent routing of pipeline
    lifecycle events, discovery requests, and processing notifications across the distributed system.

    The subject pattern encodes source/target pairs and run keys, enabling precise event filtering and
    subscription management for observability tools, monitoring dashboards, and reactive processing components.
    """

    PIPELINE_TOPIC: ClassVar[str] = "pipeline"

    def get_pipeline_discovery_subject_request(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        source_type: Annotated[str, "Pipeline source type, such as 'datalake'"],
        source_id: Annotated[str, "Pipeline source id / container name"],
        target_type: Annotated[str, "Pipeline target type, such as 'knowledge'"],
        target_id: Annotated[str, "Pipeline target id / knowledge db name"],
    ):
        return (
            f"{self.INSTANCE_DISCOVERY_TOPIC}."
            f"{self.PIPELINE_TOPIC}."
            f"{source_type}."
            f"{source_id}."
            f"to."
            f"{target_type}."
            f"{target_id}."
            f"request."
            f"{call_id}"
        )

    def get_pipeline_discovery_subject_response(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        source_type: Annotated[str, "Pipeline source type, such as 'datalake'"],
        source_id: Annotated[str, "Pipeline source id / container name"],
        target_type: Annotated[str, "Pipeline target type, such as 'knowledge'"],
        target_id: Annotated[str, "Pipeline target id / knowledge db name"],
    ):
        return (
            f"{self.INSTANCE_DISCOVERY_TOPIC}."
            f"{self.PIPELINE_TOPIC}."
            f"{source_type}."
            f"{source_id}."
            f"to."
            f"{target_type}."
            f"{target_id}."
            f"response."
            f"{call_id}"
        )

    def get_subject_for_specific_event_in_pipeline(
        self,
        source_type: Annotated[str, "Pipeline source type, such as 'datalake'"],
        source_id: Annotated[str, "Pipeline source id / container name"],
        target_type: Annotated[str, "Pipeline target type, such as 'knowledge'"],
        target_id: Annotated[str, "Pipeline target id / knowledge db name"],
        run_key: Annotated[str, "Pipeline run key"],
        event_name: Annotated[str, "Specific event name"],
        event_id: Annotated[str, "Event instance ID"],
    ) -> str:
        return (
            f"{self.PIPELINE_TOPIC}."
            f"{source_type}."
            f"{source_id}."
            f"to."
            f"{target_type}."
            f"{target_id}."
            f"{run_key}."
            f"{event_name}."
            f"{event_id}"
        )
