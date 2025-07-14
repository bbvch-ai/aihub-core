from typing import Annotated

from pydantic import Field

from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics.discovery.DiscoveryTopic import DiscoveryTopic


class ProcessDiscoveryTopic(DiscoveryTopic):
    """
    Specialization of DiscoveryTopic for process-specific discovery subjects, including process_class and process_id.

    While DiscoveryTopic covers generic discovery patterns, some discovery calls specifically target an
    process or a class of processes. AgentDiscoveryTopic provides a structured view of these more granular
    queries or responses, allowing the system to quickly identify which process (by class and ID) is involved.

    """

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
        assert topic_type == ProcessTopicManager.DISCOVERY_TOPIC, f"Unexpected topic type: {subject}"
        assert discovery_topic == ProcessTopicManager.PROCESS_TOPIC, f"Not a process discovery topic: {subject}"

        return cls(
            discovery_topic=discovery_topic,
            process_class=process_class,
            process_id=process_id,
            request_response=request_response,
            call_id=call_id,
        )
