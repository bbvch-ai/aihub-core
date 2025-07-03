from typing import Annotated, Optional, Tuple

from typing_extensions import override

from aihub_lib.nats.topic_managers.AbstractStreamTopicManager import AbstractStreamTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager


class ProcessInstanceTopicManager(ProcessTopicManager, AbstractStreamTopicManager):
    def __init__(
        self,
        process_class: Annotated[str, "The processes class identifier."],
        process_id: Annotated[str, "Unique identifier for the specific process instance."],
    ):
        super().__init__()
        self.process_class = process_class
        self.process_id = process_id

    def get_process_discovery_subject_request(
        self,
        call_id: Annotated[str, "Identifier linking request and response"],
        process_class: Optional[str] = None,
        process_id: Optional[str] = None,
    ) -> str:
        """
        Returns a subject for requesting discovery info about this process instance (or a provided override).
        If process_class/process_id are not specified, it uses the instance's own identifiers.
        """
        return super().get_process_discovery_subject_request(
            process_class=process_class or self.process_class,
            process_id=process_id or self.process_id,
            call_id=call_id,
        )

    def get_process_discovery_subject_response(
        self,
        call_id: Annotated[str, "Identifier linking request and response"],
        process_class: Optional[str] = None,
        process_id: Optional[str] = None,
    ) -> str:
        """
        Returns a subject for receiving process discovery responses for this process instance (or a provided override).
        If process_class/process_id are not specified, it uses the instance's own identifiers.
        """
        return super().get_process_discovery_subject_response(
            process_class=process_class or self.process_class,
            process_id=process_id or self.process_id,
            call_id=call_id,
        )

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

    def get_stream(self) -> Tuple[str, str]:
        return self._get_stream_name_for_all_events(), self.get_subject_for_all_events_in_process()

    def _get_stream_name_for_all_events(self) -> str:
        """Returns the stream name used for all process events."""
        return f"{self.PROCESS_TOPIC}_{self.process_class}_{self.process_id}_stream"
