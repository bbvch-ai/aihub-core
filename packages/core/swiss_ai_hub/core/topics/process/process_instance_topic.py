from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.topic_managers.process.process_topic_manager import ProcessTopicManager
from swiss_ai_hub.core.topics.process.process_class_topic import ProcessClassTopic


class ProcessInstanceTopic(ProcessClassTopic):
    process_id: Annotated[str, Field(description="Unique identifier for the specific process instance.")]

    def __str__(self) -> str:
        """Returns the full subject string for this process instance topic."""
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
    def from_process_class_topic(
        cls,
        process_class_topic: ProcessClassTopic,
        process_id: str,
    ) -> Self:
        return cls(
            process_class=process_class_topic.process_class,
            process_id=process_id,
            process_walkthrough_id=process_class_topic.process_walkthrough_id,
            event_type=process_class_topic.event_type,
            event_name=process_class_topic.event_name,
            event_id=process_class_topic.event_id,
        )
