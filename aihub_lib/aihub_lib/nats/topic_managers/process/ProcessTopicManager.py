from typing import Annotated, ClassVar

from aihub_lib.nats.topic_managers.TopicManager import TopicManager


class ProcessTopicManager(TopicManager):
    PROCESS_TOPIC: ClassVar[str] = "process"

    WORK_REQUEST_EVENT: ClassVar[str] = "work_request"
    WORK_EVENT: ClassVar[str] = "work"

    def get_process_instance_discovery_subject_request(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        process_class: Annotated[str, "Process class filter or '*'"] = "*",
        process_id: Annotated[str, "Process ID filter or or '*'"] = "*",
    ) -> str:
        """Returns a subject for requesting process discovery information."""
        return (
            f"{self.INSTANCE_DISCOVERY_TOPIC}."
            f"{self.PROCESS_TOPIC}."
            f"{process_class}."
            f"{process_id}."
            f"request."
            f"{call_id}"
        )

    def get_process_class_discovery_subject_request(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        process_class: Annotated[str, "Process class filter or '*'"] = "*",
    ) -> str:
        """Returns a subject for requesting process discovery information for a specific process class."""
        return f"{self.CLASS_DISCOVERY_TOPIC}.{self.PROCESS_TOPIC}.{process_class}.*.request.{call_id}"

    def get_process_instance_discovery_subject_response(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        process_class: Annotated[str, "Process class filter or '*'"] = "*",
        process_id: Annotated[str, "Process ID filter or or '*'"] = "*",
    ) -> str:
        """Returns a subject for receiving process discovery information."""
        return (
            f"{self.INSTANCE_DISCOVERY_TOPIC}."
            f"{self.PROCESS_TOPIC}."
            f"{process_class}."
            f"{process_id}."
            f"response."
            f"{call_id}"
        )

    def get_process_class_discovery_subject_response(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        process_class: Annotated[str, "Process class filter or '*'"] = "*",
    ) -> str:
        """Returns a subject for receiving process discovery information for a specific process class."""
        return (
            f"{self.CLASS_DISCOVERY_TOPIC}."
            f"{self.PROCESS_TOPIC}."
            f"{process_class}."
            f"*."
            f"response."
            f"{call_id}"
        )

    def get_subject_for_specific_event_in_process(
        self,
        process_class: str,
        process_id: str,
        process_walkthrough_id: str,
        event_type: str,
        event_name: str,
        event_id: str,
    ) -> str:
        """Returns a subject pinpointing a specific event in a given process run."""
        return (
            f"{self.PROCESS_TOPIC}."
            f"{process_class}."
            f"{process_id}."
            f"{process_walkthrough_id}."
            f"{event_type}."
            f"{event_name}."
            f"{event_id}"
        )

    def get_subject_for_all_events_in_process(self) -> str:
        """Returns a subject pattern matching all events from all processes."""
        return self.get_subject_for_specific_event_in_process(
            process_class="*",
            process_id="*",
            process_walkthrough_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_request_events_in_process(self) -> str:
        """Returns a subject pattern matching all control events from all processes."""
        return self.get_subject_for_specific_event_in_process(
            process_class="*",
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_REQUEST_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_events_in_process(self) -> str:
        """Returns a subject pattern matching all control events from all processes."""
        return self.get_subject_for_specific_event_in_process(
            process_class="*",
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_EVENT,
            event_name="*",
            event_id="*",
        )
