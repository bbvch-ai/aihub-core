from typing import Annotated

from pydantic import Field

from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics.process.ProcessClassTopic import ProcessClassTopic


class ProcessInstanceTopic(ProcessClassTopic):
    process_id: Annotated[str, Field(description="Unique identifier for the specific process instance.")]

    @property
    def execution_context_id(self) -> str:
        """In the domain of processes, the processes process_walkthrough_id is the narrowest scope in which
        a process topic is published and must be persisted."""
        return self.process_walkthrough_id

    def __str__(self) -> str:
        """Returns the full subject string for this agent topic."""
        return (
            f"{ProcessTopicManager.PROCESS_TOPIC}."
            f"{self.process_class}."
            f"{self.process_id}."
            f"{self.process_walkthrough_id}."
            f"{self.event_type}."
            f"{self.event_name}."
            f"{self.event_id}"
        )

    @classmethod
    def from_subject(cls, subject: str) -> "ProcessInstanceTopic":
        """
        Constructs a ProcessTopic from a subject string that may contain wildcards.
        """
        (
            topic_type,
            process_class,
            process_id,
            process_walkthrough_id,
            event_type,
            event_name,
            event_id,
        ) = subject.split(".")
        assert topic_type == ProcessTopicManager.PROCESS_TOPIC, f"Unexpected topic type in subject: {subject}"

        return cls(
            process_class=process_class,
            process_id=process_id,
            process_walkthrough_id=process_walkthrough_id,
            event_type=event_type,
            event_name=event_name,
            event_id=event_id,
        )

    @classmethod
    def from_process_class_topic(
        cls,
        process_class_topic: ProcessClassTopic,
        process_id: str,
    ) -> "ProcessInstanceTopic":
        return cls(
            process_class=process_class_topic.process_class,
            process_id=process_id,
            process_walkthrough_id=process_class_topic.process_walkthrough_id,
            event_type=process_class_topic.event_type,
            event_name=process_class_topic.event_name,
            event_id=process_class_topic.event_id,
        )
