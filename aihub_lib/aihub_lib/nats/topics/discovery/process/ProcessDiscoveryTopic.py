from typing import Annotated

from pydantic import Field

from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics.discovery.DiscoveryTopic import DiscoveryTopic


class ProcessDiscoveryTopic(DiscoveryTopic):
    process_class: Annotated[str, Field(description="Process class targeted by the discovery.")]
    process_id: Annotated[str, Field(description="Specific Process instance targeted by the discovery.")]

    @classmethod
    def from_subject(cls, subject: str) -> "ProcessDiscoveryTopic":
        """
        Use this when dealing with process-specific discovery subjects to extract process_class and process_id.
        """
        (
            topic_type,
            discovery_topic,
            process_class,
            process_id,
            request_response,
            call_id,
        ) = subject.split(".")
        assert topic_type == TopicManager.DISCOVERY_TOPIC, f"Unexpected topic type: {subject}"
        assert discovery_topic == TopicManager.PROCESS_TOPIC, f"Not a process discovery topic: {subject}"

        return cls(
            discovery_topic=discovery_topic,
            process_class=process_class,
            process_id=process_id,
            request_response=request_response,
            call_id=call_id,
        )
