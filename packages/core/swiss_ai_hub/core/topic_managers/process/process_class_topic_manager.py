from typing import Annotated, override

from pydantic import Field

from swiss_ai_hub.core.topic_managers.abstract_stream_topic_manager import AbstractStreamTopicManager
from swiss_ai_hub.core.topic_managers.process.process_topic_manager import ProcessTopicManager


class ProcessClassTopicManager(ProcessTopicManager, AbstractStreamTopicManager):
    process_class: Annotated[str, Field(description="The processes class identifier.")]

    def get_subject_for_specific_event_in_process_class(
        self,
        process_id: Annotated[str, "Unique identifier for the specific process instance."],
        process_walkthrough_id: Annotated[str, "Walkthrough ID within the thread"],
        event_type: Annotated[str, "Event type (e.g., display_event, control_event)"],
        event_name: Annotated[str, "Specific event name"],
        event_id: Annotated[str, "Event instance ID"],
    ) -> str:
        """Returns a subject for a specific event from this process class, narrowed by process_walkthrough_id."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id=process_id,
            process_walkthrough_id=process_walkthrough_id,
            event_type=event_type,
            event_name=event_name,
            event_id=event_id,
        )

    def get_subject_for_all_work_request_events_within_process_class(self) -> str:
        """Returns a subject pattern matching all work events within this process class."""
        return self.get_subject_for_specific_event_in_process_class(
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_REQUEST_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_events_within_process_class(self) -> str:
        """Returns a subject pattern matching all work events within this process class."""
        return self.get_subject_for_specific_event_in_process_class(
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_EVENT,
            event_name="*",
            event_id="*",
        )

    @override
    def get_subject_for_all_control_events(self) -> str:
        return self.get_subject_for_all_work_events_within_process_class()

    def get_subject_for_all_events_in_process(self) -> str:
        """Returns a subject pattern matching all events from all process."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id="*",
            process_walkthrough_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_request_events_in_process(self) -> str:
        """Returns a subject pattern matching all work request events from all process."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_REQUEST_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_events_in_process(self) -> str:
        """Returns a subject pattern matching all work events from all process."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_stream(self) -> tuple[str, str]:
        return self._get_stream_name_for_all_events(), self._get_subject_for_all_events_in_process_class()

    def _get_stream_name_for_all_events(self) -> str:
        """Returns the stream name used for all process events."""
        return f"{self.PROCESS_TOPIC}_{self.process_class}_stream"

    def _get_subject_for_all_events_in_process_class(self) -> str:
        """Returns a subject pattern matching all events from this process class."""
        return self.get_subject_for_specific_event_in_process_class(
            process_id="*",
            process_walkthrough_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )
