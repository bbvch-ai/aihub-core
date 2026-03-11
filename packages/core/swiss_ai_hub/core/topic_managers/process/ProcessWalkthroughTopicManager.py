from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager
from swiss_ai_hub.core.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from swiss_ai_hub.core.topics.process.ProcessInstanceTopic import ProcessInstanceTopic


class ProcessWalkthroughTopicManager(ProcessClassTopicManager):
    process_id: Annotated[str | None, Field(description="Unique identifier for the specific process instance.")]
    process_walkthrough_id: Annotated[str, Field(description="Unique identifier for the specific process walkthrough.")]

    def get_subject_for_work_request_event_in_walkthrough(
        self,
        event_name: Annotated[str, "Name of the control event"],
        event_id: Annotated[str | None, "Specific event instance ID or '*'"] = "*",
    ) -> str:
        """Returns a subject pattern for work request events of a given name within this walkthrough."""
        return self.get_subject_for_specific_event_in_process_class(
            process_id=self.process_id or "*",
            process_walkthrough_id=self.process_walkthrough_id,
            event_type=self.WORK_REQUEST_EVENT,
            event_name=event_name,
            event_id=event_id,
        )

    def get_subject_for_work_event_in_walkthrough(
        self,
        event_name: Annotated[str, "Name of the display event"],
        event_id: Annotated[str | None, "Specific event instance ID or '*'"] = "*",
    ) -> str:
        """Returns a subject pattern for work events of a given name within this walkthrough."""
        return self.get_subject_for_specific_event_in_process_class(
            process_id=self.process_id or "*",
            process_walkthrough_id=self.process_walkthrough_id,
            event_type=self.WORK_EVENT,
            event_name=event_name,
            event_id=event_id,
        )

    @classmethod
    def from_process_instance_topic_manager(
        cls,
        topic_manager: ProcessInstanceTopicManager,
        process_walkthrough_id: Annotated[str, "walkthrough ID"],
    ) -> Self:
        """
        Creates a ProcessWalkthroughTopicManager from an existing
        processInstanceTopicManager and additional walkthrough details.
        """
        return cls(
            process_class=topic_manager.process_class,
            process_id=topic_manager.process_id,
            process_walkthrough_id=process_walkthrough_id,
        )

    @classmethod
    def from_process_class_topic_manager(
        cls,
        topic_manager: ProcessClassTopicManager,
        process_walkthrough_id: Annotated[str, "walkthrough ID"],
        process_id: Annotated[str | None, "Optional process ID"] = None,
    ) -> Self:
        """
        Creates a ProcessWalkthroughTopicManager from an existing
        processClassTopicManager and additional walkthrough details.
        """
        return cls(
            process_class=topic_manager.process_class,
            process_id=process_id,
            process_walkthrough_id=process_walkthrough_id,
        )

    @classmethod
    def from_process_topic(cls, topic: ProcessInstanceTopic) -> Self:
        """Constructs an ProcessWalkthroughTopicManager directly from an processTopic object."""
        return cls(
            process_class=topic.process_class,
            process_id=topic.process_id,
            process_walkthrough_id=topic.process_walkthrough_id,
        )
