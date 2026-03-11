from typing import Annotated, override

from pydantic import Field

from swiss_ai_hub.core.topic_managers.AbstractStreamTopicManager import AbstractStreamTopicManager
from swiss_ai_hub.core.topic_managers.pipeline.PipelineTopicManager import PipelineTopicManager


class PipelineInstanceTopicManager(PipelineTopicManager, AbstractStreamTopicManager):
    """
    Topic manager bound to a specific pipeline instance with pre-configured source and target endpoints.

    Simplifies event routing for a particular pipeline by maintaining the source/target context,
    eliminating the need to repeatedly specify these parameters for each operation. This is particularly
    useful for long-running pipelines or sensors that continuously monitor a specific data flow, ensuring
    events are consistently routed to the correct JetStream subjects and consumers.
    """

    source_type: Annotated[str, Field(description="The pipeline source type, such as 'datalake'")]
    source_id: Annotated[str, Field(description="The pipeline source identifier")]
    target_type: Annotated[str, Field(description="The pipeline target type, such as 'datalake'")]
    target_id: Annotated[str, Field(description="The pipeline target identifier")]

    def get_pipeline_instance_discovery_subject_request(
        self,
        call_id: Annotated[str, "Identifier linking request and response"],
        source_type: Annotated[str, "Pipeline source type, such as 'datalake'"],
        source_id: Annotated[str, "Pipeline source id / container name"],
        target_type: Annotated[str, "Pipeline target type, such as 'knowledge'"],
        target_id: Annotated[str, "Pipeline target id / knowledge db name"],
    ) -> str:
        return super().get_pipeline_discovery_subject_request(
            source_type=source_type or self.source_type,
            source_id=source_id or self.source_id,
            target_type=target_type or self.target_type,
            target_id=target_id or self.target_id,
            call_id=call_id,
        )

    def get_pipeline_discovery_subject_response(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        source_type: Annotated[str, "Pipeline source type, such as 'datalake'"],
        source_id: Annotated[str, "Pipeline source id / container name"],
        target_type: Annotated[str, "Pipeline target type, such as 'knowledge'"],
        target_id: Annotated[str, "Pipeline target id / knowledge db name"],
    ) -> str:
        return super().get_pipeline_discovery_subject_response(
            source_type=source_type or self.source_type,
            source_id=source_id or self.source_id,
            target_type=target_type or self.target_type,
            target_id=target_id or self.target_id,
            call_id=call_id,
        )

    def get_subject_for_specific_event_in_pipeline_instance(
        self,
        run_key: Annotated[str, "Pipeline run key"],
        event_name: Annotated[str, "Specific event name"],
        event_id: Annotated[str, "Event instance ID"],
    ) -> str:
        return self.get_subject_for_specific_event_in_pipeline(
            source_type=self.source_type,
            source_id=self.source_id,
            target_type=self.target_type,
            target_id=self.target_id,
            run_key=run_key,
            event_name=event_name,
            event_id=event_id,
        )

    @override
    def get_stream(self) -> tuple[str, str]:
        return self._get_stream_name_for_all_events(), self._get_subject_for_all_events_in_pipeline_instance()

    def _get_stream_name_for_all_events(self) -> str:
        return f"{self.PIPELINE_TOPIC}_{self.source_type}_{self.source_id}_{self.target_type}_{self.target_id}_stream"

    def _get_subject_for_all_events_in_pipeline_instance(self) -> str:
        return self.get_subject_for_specific_event_in_pipeline_instance(
            run_key="*",
            event_name="*",
            event_id="*",
        )

    @override
    def get_subject_for_all_control_events(self) -> str:
        return self.get_subject_for_specific_event_in_pipeline_instance(
            run_key="*",
            event_name="*",
            event_id="*",
        )
