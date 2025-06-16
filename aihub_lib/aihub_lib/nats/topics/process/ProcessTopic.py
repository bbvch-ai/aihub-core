from pydantic import Field

from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics.Topic import Topic


class ProcessTopic(Topic):
    process_class: str = Field(..., description="The processes class identifier.")
    process_id: str = Field(..., description="Unique identifier for the specific process instance.")

    process_walkthrough_id: str = Field(..., description="Unique identifier for this specific process walk through.")

    event_type: str = Field(..., description="Type of event (e.g., 'display_event', 'control_event').")
    event_name: str = Field(
        ..., description="Name of the event (e.g., 'StartEvent', 'StopEvent', 'ExceptionEvent, ...')."
    )
    event_id: str = Field(..., description="Unique identifier for this particular event instance.")

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
    def from_subject(cls, subject: str) -> "ProcessTopic":
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