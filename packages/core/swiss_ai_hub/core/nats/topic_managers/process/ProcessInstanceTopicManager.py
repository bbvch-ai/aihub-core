from typing import Annotated, override

from pydantic import Field

from swiss_ai_hub.core.nats.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager


class ProcessInstanceTopicManager(ProcessClassTopicManager):
    process_id: Annotated[str, Field(description="Unique identifier for the specific process instance.")]

    def get_subject_for_specific_event_in_process_instance(
        self,
        process_walkthrough_id: Annotated[str, "Walkthrough ID within the thread"],
        event_type: Annotated[str, "Event type (e.g., display_event, control_event)"],
        event_name: Annotated[str, "Specific event name"],
        event_id: Annotated[str, "Event instance ID"],
    ) -> str:
        """Returns a subject for a specific event from this process instance, narrowed by process_walkthrough_id."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id=self.process_id,
            process_walkthrough_id=process_walkthrough_id,
            event_type=event_type,
            event_name=event_name,
            event_id=event_id,
        )

    def get_subject_for_everything_within_process_instance(self) -> str:
        """Returns a subject pattern for all events in this process instance, regardless of process_walkthrough_id."""
        return self.get_subject_for_specific_event_in_process_instance(
            process_walkthrough_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_request_events_within_process_instance(self) -> str:
        """Returns a subject pattern matching all work events within this process instance."""
        return self.get_subject_for_specific_event_in_process_instance(
            process_walkthrough_id="*",
            event_type=self.WORK_REQUEST_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_events_within_process_instance(self) -> str:
        """Returns a subject pattern matching all work events within this process instance."""
        return self.get_subject_for_specific_event_in_process_instance(
            process_walkthrough_id="*",
            event_type=self.WORK_EVENT,
            event_name="*",
            event_id="*",
        )

    @override
    def get_subject_for_all_control_events(self) -> str:
        return self.get_subject_for_all_work_events_within_process_instance()

    def get_subject_for_all_events_in_process(self) -> str:
        """Returns a subject pattern matching all events from all process."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id=self.process_id,
            process_walkthrough_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_request_events_in_process(self) -> str:
        """Returns a subject pattern matching all work request events from all process."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id=self.process_id,
            process_walkthrough_id="*",
            event_type=self.WORK_REQUEST_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_events_in_process(self) -> str:
        """Returns a subject pattern matching all work events from all process."""
        return self.get_subject_for_specific_event_in_process(
            process_class=self.process_class,
            process_id=self.process_id,
            process_walkthrough_id="*",
            event_type=self.WORK_EVENT,
            event_name="*",
            event_id="*",
        )
