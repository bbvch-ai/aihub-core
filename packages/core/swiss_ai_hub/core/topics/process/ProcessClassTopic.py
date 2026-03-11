from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from swiss_ai_hub.core.topics.process.PartialProcessTopic import PartialProcessTopic


class ProcessClassTopic(PartialProcessTopic):
    process_class: Annotated[str, Field(description="The processes class identifier.")]

    process_walkthrough_id: Annotated[
        str, Field(description="Unique identifier for this specific process walk through.")
    ]

    event_type: Annotated[str, Field(description="Type of event (e.g., 'display_event', 'control_event').")]
    event_name: Annotated[
        str, Field(description="Name of the event (e.g., 'StartEvent', 'StopEvent', 'ExceptionEvent, ...').")
    ]
    event_id: Annotated[str, Field(description="Unique identifier for this particular event instance.")]

    def __str__(self) -> str:
        """Returns the full subject string for this process topic."""
        return (
            f"{ProcessTopicManager.PROCESS_TOPIC}."
            f"{self.process_class}."
            f"*."
            f"{self.process_walkthrough_id}."
            f"{self.event_type}."
            f"{self.event_name}."
            f"{self.event_id}"
        )
